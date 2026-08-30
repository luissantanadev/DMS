from django.urls import re_path

from .consumers import PainelConsumer

websocket_urlpatterns = [
    re_path(r"ws/painel/$", PainelConsumer.as_asgi()),
]
