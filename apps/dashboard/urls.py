from django.urls import path
from .views import box, finalizar_movimentacao, painel, portaria, selecionar_area

urlpatterns = [
    path("acesso/", selecionar_area, name="selecionar_area"),
    path("", painel, name="painel"),
    path("box/", box, name="box"),
    path("portaria/", portaria, name="portaria"),
    path("portaria/finalizar/<int:movimentacao_id>/", finalizar_movimentacao, name="finalizar_movimentacao"),
]
