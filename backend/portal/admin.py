from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Visitante

@admin.register(Visitante)
class VisitanteAdmin(ImportExportModelAdmin): 
    list_display = ('nombre', 'empresa', 'motivo', 'mac_address', 'fecha_registro')
    
    list_filter = ('fecha_registro', 'empresa', 'motivo')
    
    search_fields = ('nombre', 'email', 'mac_address', 'empresa')
    
    ordering = ('-fecha_registro',)