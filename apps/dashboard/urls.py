from django.urls import path
from .views import box, painel, portaria, selecionar_area

urlpatterns = [
    path("acesso/", selecionar_area, name="selecionar_area"),
    path("", painel, name="painel"),
    path("box/", box, name="box"),
    path("portaria/", portaria, name="portaria"),
]
