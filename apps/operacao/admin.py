from django.contrib import admin

from .models import Movimentacao


@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    list_display = (
        "placa",
        "transportadora",
        "doca",
        "tipo_operacao",
        "status",
        "criado_em",
    )
    list_filter = ("status", "tipo_operacao")
    search_fields = ("placa", "motorista_nome", "carga")
