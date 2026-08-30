import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from apps.dashboard.views import _build_painel_data


class PainelConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if not self.scope["user"].is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add("painel_status", self.channel_name)
        await self.accept()

        payload = await database_sync_to_async(_build_painel_data)(self.scope["user"])
        await self.send(text_data=json.dumps({
            "docas": payload["docas"],
            "docas_livres": payload["docas_livres"],
            "docas_ocupadas": payload["docas_ocupadas"],
            "alertas": payload["alertas"],
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("painel_status", self.channel_name)

    async def painel_status(self, event):
        await self.send(text_data=json.dumps(event["payload"]))
