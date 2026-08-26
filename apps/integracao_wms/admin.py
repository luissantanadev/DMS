from django.contrib import admin
from .models import SincronizacaoWMS


@admin.register(SincronizacaoWMS)
class SincronizacaoWMSAdmin(admin.ModelAdmin):
    list_display = ('shipment_id', 'status', 'operador_wms', 'criado_em')
    list_filter = ('status', 'criado_em')
    search_fields = ('shipment_id', 'operador_wms')
    readonly_fields = ('shipment_id', 'dados_wms', 'dados_mapeados', 'criado_em', 'atualizado_em')
    
    fieldsets = (
        ('Informações de Sincronização', {
            'fields': ('shipment_id', 'status', 'movimentacao')
        }),
        ('Dados do WMS', {
            'fields': ('dados_wms', 'operador_wms', 'localizacao_wms')
        }),
        ('Dados Mapeados', {
            'fields': ('dados_mapeados',)
        }),
        ('Erros', {
            'fields': ('mensagem_erro',),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
