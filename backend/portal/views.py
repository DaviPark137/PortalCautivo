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

def unifi_authorize_guest(mac_address):
    """
    Ordena al UniFi Controller local en Lightsail que libere el acceso a internet para la MAC del visitante.
    """
    if not mac_address or mac_address in ('00:00:00:00:00:00', 'undefined', 'null'):
        return False

    unifi_user = os.environ.get('UNIFI_USER', 'portal_admin')
    unifi_pass = os.environ.get('UNIFI_PASSWORD', '')
    unifi_host = os.environ.get('UNIFI_HOST', 'https://172.17.0.1:8443') # Host gateway desde Docker

    # Si no se configuró contraseña en .env, no intentamos llamar a la API
    if not unifi_pass:
        print("[UniFi] No UNIFI_PASSWORD configurado en el servidor.")
        return False

    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        cj = CookieJar()
        opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cj),
            urllib.request.HTTPSHandler(context=ctx)
        )

        # 1. Login a la API de UniFi Controller
        login_url = f"{unifi_host}/api/login"
        login_data = json.dumps({"username": unifi_user, "password": unifi_pass}).encode('utf-8')
        req_login = urllib.request.Request(
            login_url,
            data=login_data,
            headers={'Content-Type': 'application/json'}
        )
        opener.open(req_login, timeout=5)

        # 2. Ordenar autorización del dispositivo por su MAC (1440 minutos = 24 horas)
        auth_url = f"{unifi_host}/api/s/default/cmd/stamgr"
        auth_data = json.dumps({
            "cmd": "authorize-guest",
            "mac": mac_address.lower(),
            "minutes": 1440
        }).encode('utf-8')
        req_auth = urllib.request.Request(
            auth_url,
            data=auth_data,
            headers={'Content-Type': 'application/json'}
        )
        with opener.open(req_auth, timeout=5) as resp:
            print(f"[UniFi] MAC {mac_address} autorizada exitosamente con código {resp.status}")
            return resp.status == 200
    except Exception as e:
        print(f"[UniFi Error] Error autorizando MAC {mac_address}: {e}")
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