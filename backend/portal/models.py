from django.db import models

class Visitante(models.Model):
    nombre = models.CharField(max_length=255)
    email = models.EmailField()
    motivo = models.CharField(max_length=100)
    empresa = models.CharField(max_length=100)
    mac_address = models.CharField(max_length=50, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} - {self.empresa} ({self.mac_address})"