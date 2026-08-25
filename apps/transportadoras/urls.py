from django.urls import path

from .views import api_transportadoras, lista_transportadoras

urlpatterns = [
    path("", lista_transportadoras, name="lista_transportadoras"),
    path("api/", api_transportadoras, name="api_transportadoras"),
]
