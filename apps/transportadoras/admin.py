from django.contrib import admin

from .models import Transportadora


@admin.register(Transportadora)
class TransportadoraAdmin(admin.ModelAdmin):
    list_display = ("nome_fantasia", "razao_social", "cnpj", "ativa")
    list_filter = ("ativa",)
    search_fields = ("nome_fantasia", "razao_social", "cnpj")
