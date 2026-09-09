import os
import json
import ssl
import urllib.request
from http.cookiejar import CookieJar
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Visitante
from .serializers import VisitanteSerializer

import re

def get_docker_gateway():
    """
    Detecta la IP de la puerta de enlace (Host) dentro de un contenedor Linux en Docker.
    """
    try:
        with open("/proc/net/route") as fh:
            for line in fh:
                fields = line.strip().split()
                if len(fields) >= 3 and fields[1] == '00000000':
                    import socket, struct
                    return socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))
    except Exception:
        pass
    return None

def unifi_authorize_guest(mac_address, ap_mac=None):
    """
    Ordena al UniFi Controller en el servidor Lightsail que autorice el acceso a internet para la MAC del visitante.
    """
    if not mac_address:
        print("[UniFi] MAC no proporcionada. No se puede autorizar.", flush=True)
        return False

    # Limpiar y normalizar formato de MAC (aa:bb:cc:dd:ee:ff)
    mac_clean = mac_address.strip().lower().replace('-', ':')
    if len(mac_clean) == 12 and ':' not in mac_clean:
        mac_clean = ':'.join(mac_clean[i:i+2] for i in range(0, 12, 2))

    # Validar formato MAC
    if not re.match(r'^([0-9a-f]{2}[:]){5}([0-9a-f]{2})$', mac_clean) or mac_clean == '00:00:00:00:00:00':
        print(f"[UniFi] MAC '{mac_address}' inválida o genérica. No se puede autorizar en UniFi.", flush=True)
        return False

    unifi_api_key = os.environ.get('UNIFI_API_KEY', '').strip()
    unifi_user = os.environ.get('UNIFI_USER', 'portal_admin').strip()
    unifi_pass = os.environ.get('UNIFI_PASSWORD', '').strip()
    unifi_site = os.environ.get('UNIFI_SITE', 'default').strip()

    if not unifi_api_key and not unifi_pass:
        print("[UniFi Advertencia] No se configuró UNIFI_PASSWORD ni UNIFI_API_KEY en .env del servidor.", flush=True)
        return False

    # Lista de endpoints a intentar para conectar al UniFi Controller en el Host
    candidate_hosts = []
    env_host = os.environ.get('UNIFI_HOST')
    if env_host:
        candidate_hosts.append(env_host.rstrip('/'))

    # Host gateway detectado dinámicamente desde Docker
    gw = get_docker_gateway()
    if gw:
        candidate_hosts.append(f"https://{gw}:8443")

    # Fallbacks conocidos
    fallbacks = [
        'https://host.docker.internal:8443',
        'https://3.21.22.115:8443',
        'https://172.17.0.1:8443',
        'https://127.0.0.1:8443'
    ]
    for fb in fallbacks:
        if fb not in candidate_hosts:
            candidate_hosts.append(fb)

    print(f"[UniFi] Intentando autorizar MAC: {mac_clean} (AP: {ap_mac}) usando usuario: '{unifi_user}'...", flush=True)

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    for host in candidate_hosts:
        # MÉTODO 1: Si hay API KEY configurada (UniFi Network 9 / 10)
        if unifi_api_key:
            try:
                auth_url = f"{host}/api/s/{unifi_site}/cmd/stamgr"
                auth_data = {
                    "cmd": "authorize-guest",
                    "mac": mac_clean,
                    "minutes": 1440
                }
                if ap_mac and ap_mac not in ('', 'undefined', 'null'):
                    auth_data["ap_mac"] = ap_mac.strip().lower().replace('-', ':')

                auth_payload = json.dumps(auth_data).encode('utf-8')
                auth_headers = {
                    'Content-Type': 'application/json',
                    'X-API-KEY': unifi_api_key,
                    'User-Agent': 'PortalCautivoBackend'
                }
                req_auth = urllib.request.Request(auth_url, data=auth_payload, headers=auth_headers)
                with urllib.request.urlopen(req_auth, context=ctx, timeout=5) as resp_auth:
                    body_resp = resp_auth.read().decode('utf-8')
                    print(f"[UniFi Éxito API-KEY] MAC {mac_clean} autorizada en {host}. Respuesta: {body_resp}", flush=True)
                    return True
            except Exception as e:
                print(f"[UniFi API-KEY Error] en {host}: {e}", flush=True)

        # MÉTODO 2: Autenticación por Usuario y Contraseña
        cj = CookieJar()
        opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cj),
            urllib.request.HTTPSHandler(context=ctx)
        )

        login_success = False
        csrf_token = None

        for login_path in ['/api/login', '/api/auth/login']:
            try:
                login_url = f"{host}{login_path}"
                login_payload = json.dumps({
                    "username": unifi_user,
                    "password": unifi_pass,
                    "remember": True
                }).encode('utf-8')
                req_login = urllib.request.Request(
                    login_url,
                    data=login_payload,
                    headers={'Content-Type': 'application/json', 'User-Agent': 'PortalCautivoBackend'}
                )

                with opener.open(req_login, timeout=4) as resp_login:
                    if resp_login.status == 200:
                        login_success = True
                        csrf_token = (
                            resp_login.headers.get('X-CSRF-Token') or 
                            resp_login.headers.get('x-csrf-token') or 
                            resp_login.headers.get('csrf_token')
                        )
                        if not csrf_token:
                            for cookie in cj:
                                if 'csrf' in cookie.name.lower():
                                    csrf_token = cookie.value
                                    break
                        print(f"[UniFi] Login exitoso en {host}{login_path}. CSRF: {'Sí' if csrf_token else 'No'}", flush=True)
                        break
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    continue # Probar el siguiente path de login
                try:
                    err_detail = e.read().decode('utf-8')
                except Exception:
                    err_detail = ""
                print(f"[UniFi Error Login HTTP {e.code}] en {host}{login_path}: {err_detail}", flush=True)
                break
            except Exception as e:
                # No se pudo conectar a este host
                break

        if not login_success:
            continue

        # 2. Enviar comando authorize-guest (24 horas = 1440 minutos)
        try:
            auth_url = f"{host}/api/s/{unifi_site}/cmd/stamgr"
            auth_data = {
                "cmd": "authorize-guest",
                "mac": mac_clean,
                "minutes": 1440
            }
            if ap_mac and ap_mac not in ('', 'undefined', 'null'):
                auth_data["ap_mac"] = ap_mac.strip().lower().replace('-', ':')

            auth_payload = json.dumps(auth_data).encode('utf-8')

            auth_headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'PortalCautivoBackend'
            }
            if csrf_token:
                auth_headers['X-CSRF-Token'] = csrf_token

            req_auth = urllib.request.Request(auth_url, data=auth_payload, headers=auth_headers)

            with opener.open(req_auth, timeout=5) as resp_auth:
                body_resp = resp_auth.read().decode('utf-8')
                print(f"[UniFi Exito] MAC {mac_clean} autorizada en {host}. Respuesta: {body_resp}", flush=True)
                return True

        except urllib.error.HTTPError as e:
            try:
                err_detail = e.read().decode('utf-8')
            except Exception:
                err_detail = ""
            print(f"[UniFi Error Auth HTTP {e.code}] en {auth_url}: {err_detail}", flush=True)
            continue
        except Exception as e:
            print(f"[UniFi Error Auth] en {host}: {e}", flush=True)
            continue

    print(f"[UniFi Error] No fue posible autorizar la MAC {mac_clean} en ningún host de UniFi.", flush=True)
    return False

@api_view(['POST'])
def registrar_visitante(request):
    """
    Recibe los datos de React y crea un nuevo visitante en la base de datos
    utilizando un Serializer para validación segura.
    """
    print(f"[Backend Registro] Datos recibidos: {request.data}", flush=True)
    serializer = VisitanteSerializer(data=request.data)
    
    if serializer.is_valid():
        visitante = serializer.save()
        
        # Intentar autorizar en UniFi automáticamente si recibimos MAC
        client_mac = request.data.get('clientMac', '')
        ap_mac = request.data.get('apMac', None)
        unifi_ok = unifi_authorize_guest(client_mac, ap_mac=ap_mac)
        
        return Response(
            {
                "mensaje": "Registro exitoso", 
                "id": visitante.id,
                "unifi_authorized": unifi_ok
            }, 
            status=status.HTTP_201_CREATED
        )
    else:
        return Response(
            {"error": "Datos inválidos", "detalles": serializer.errors}, 
            status=status.HTTP_400_BAD_REQUEST
        )