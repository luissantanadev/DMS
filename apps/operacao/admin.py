from django.contrib import admin

from .models import Motorista, Movimentacao, Veiculo


@admin.register(Motorista)
class MotoristaAdmin(admin.ModelAdmin):
    list_display = ("nome", "cpf", "telefone", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome", "cpf")


@admin.register(Veiculo)
class VeiculoAdmin(admin.ModelAdmin):
    list_display = ("placa", "modelo", "ano", "ativo")
    list_filter = ("ativo",)
    search_fields = ("placa", "modelo")


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
