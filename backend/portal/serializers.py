from rest_framework import serializers
from .models import Visitante

class VisitanteSerializer(serializers.ModelSerializer):
    clientMac = serializers.CharField(source='mac_address', required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Visitante
        fields = ['nombre', 'email', 'motivo', 'empresa', 'clientMac']
