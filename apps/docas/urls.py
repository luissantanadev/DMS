from django.urls import path
from .views import gerenciar_docas, lista_docas

urlpatterns = [
    path("", lista_docas, name="lista_docas"),
    path("gerenciar/", gerenciar_docas, name="gerenciar_docas"),
]
