from django.urls import path
from .views import (
    box,
    finalizar_movimentacao,
    gerenciar_historico,
    gerenciar_motoristas,
    gerenciar_relatorios,
    gerenciar_veiculos,
    painel,
    portaria,
    selecionar_area,
)

urlpatterns = [
    path("acesso/", selecionar_area, name="selecionar_area"),
    path("", painel, name="painel"),
    path("box/", box, name="box"),
    path("box/historico/", gerenciar_historico, name="gerenciar_historico"),
    path("box/relatorios/", gerenciar_relatorios, name="gerenciar_relatorios"),
    path("box/motoristas/", gerenciar_motoristas, name="gerenciar_motoristas"),
    path("box/veiculos/", gerenciar_veiculos, name="gerenciar_veiculos"),
    path("portaria/", portaria, name="portaria"),
    path("portaria/finalizar/<int:movimentacao_id>/", finalizar_movimentacao, name="finalizar_movimentacao"),
]
