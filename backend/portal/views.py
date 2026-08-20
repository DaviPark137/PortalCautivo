from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Visitante
from .serializers import VisitanteSerializer

@api_view(['POST'])
def registrar_visitante(request):
    """
    Recibe los datos de React y crea un nuevo visitante en la base de datos
    utilizando un Serializer para validación segura.
    """
    serializer = VisitanteSerializer(data=request.data)
    
    if serializer.is_valid():
        visitante = serializer.save()
        return Response(
            {"mensaje": "Registro exitoso", "id": visitante.id}, 
            status=status.HTTP_201_CREATED
        )
    else:
        return Response(
            {"error": "Datos inválidos", "detalles": serializer.errors}, 
            status=status.HTTP_400_BAD_REQUEST
        )