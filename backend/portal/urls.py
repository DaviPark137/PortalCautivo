from django.urls import path
from . import views

urlpatterns = [
    path('api/registro/', views.registrar_visitante, name='registro_api'),
]   