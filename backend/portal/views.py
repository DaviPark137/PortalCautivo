from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Visitante

@api_view(['POST'])
def registrar_visitante(request):
    """
    Recibe los datos de React y crea un nuevo visitante en la base de datos.
    """
    data = request.data
    
    try:
        # Guardamos el registro en PostgreSQL
        nuevo_visitante = Visitante.objects.create(
            nombre=data.get('nombre'),
            email=data.get('email'),
            motivo=data.get('motivo'),
            empresa=data.get('empresa'),
            mac_address=data.get('clientMac', 'Desconocida')
        )
        
        return Response(
            {"mensaje": "Registro exitoso", "id": nuevo_visitante.id}, 
            status=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )