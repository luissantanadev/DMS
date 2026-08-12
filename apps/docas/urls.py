from django.urls import path
from .views import lista_docas

urlpatterns = [
    path("", lista_docas, name="lista_docas"),
]
