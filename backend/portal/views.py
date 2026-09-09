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

def unifi_authorize_guest(mac_address):
    """
    Ordena al UniFi Controller en el servidor Lightsail que autorice el acceso a internet para la MAC del visitante.
    """
    if not mac_address:
        print("[UniFi] MAC no proporcionada. No se puede autorizar.")
        return False

    # Limpiar y normalizar formato de MAC (aa:bb:cc:dd:ee:ff)
    mac_clean = mac_address.strip().lower().replace('-', ':')
    if len(mac_clean) == 12 and ':' not in mac_clean:
        mac_clean = ':'.join(mac_clean[i:i+2] for i in range(0, 12, 2))

    # Validar formato MAC
    if not re.match(r'^([0-9a-f]{2}[:]){5}([0-9a-f]{2})$', mac_clean) or mac_clean == '00:00:00:00:00:00':
        print(f"[UniFi] MAC '{mac_address}' inválida o genérica. No se puede autorizar en UniFi.")
        return False

    unifi_user = os.environ.get('UNIFI_USER', 'portal_admin')
    unifi_pass = os.environ.get('UNIFI_PASSWORD', '')
    unifi_site = os.environ.get('UNIFI_SITE', 'default')

    if not unifi_pass:
        print("[UniFi] Advertencia: UNIFI_PASSWORD no está configurado en las variables de entorno.")
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

    print(f"[UniFi] Intentando autorizar MAC: {mac_clean} en UniFi...")

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    for host in candidate_hosts:
        try:
            cj = CookieJar()
            opener = urllib.request.build_opener(
                urllib.request.HTTPCookieProcessor(cj),
                urllib.request.HTTPSHandler(context=ctx)
            )

            # 1. Login en UniFi Controller
            login_url = f"{host}/api/login"
            login_payload = json.dumps({"username": unifi_user, "password": unifi_pass}).encode('utf-8')
            req_login = urllib.request.Request(
                login_url,
                data=login_payload,
                headers={'Content-Type': 'application/json', 'User-Agent': 'PortalCautivoBackend'}
            )

            with opener.open(req_login, timeout=4) as resp_login:
                if resp_login.status != 200:
                    continue

                # Extraer token CSRF si UniFi lo requiere
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

            # 2. Enviar comando authorize-guest (24 horas = 1440 minutos)
            auth_url = f"{host}/api/s/{unifi_site}/cmd/stamgr"
            auth_payload = json.dumps({
                "cmd": "authorize-guest",
                "mac": mac_clean,
                "minutes": 1440
            }).encode('utf-8')

            auth_headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'PortalCautivoBackend'
            }
            if csrf_token:
                auth_headers['X-CSRF-Token'] = csrf_token

            req_auth = urllib.request.Request(auth_url, data=auth_payload, headers=auth_headers)

            with opener.open(req_auth, timeout=5) as resp_auth:
                body_resp = resp_auth.read().decode('utf-8')
                print(f"[UniFi Exito] MAC {mac_clean} autorizada en {host}. Respuesta: {body_resp}")
                return True

        except Exception as e:
            print(f"[UniFi] No se pudo conectar a {host}: {e}")
            continue

    print(f"[UniFi Error] No fue posible autorizar la MAC {mac_clean} en ningún host de UniFi.")
    return False

@api_view(['POST'])
def registrar_visitante(request):
    """
    Recibe los datos de React y crea un nuevo visitante en la base de datos
    utilizando un Serializer para validación segura.
    """
    serializer = VisitanteSerializer(data=request.data)
    
    if serializer.is_valid():
        visitante = serializer.save()
        
        # Intentar autorizar en UniFi automáticamente si recibimos MAC
        client_mac = request.data.get('clientMac', '')
        unifi_ok = unifi_authorize_guest(client_mac)
        
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