import json
from channels.generic.websocket import AsyncWebsocketConsumer


class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Subscribe this socket to the dashboard group
        await self.channel_layer.group_add("dashboard", self.channel_name)
        await self.accept()
        await self.send(json.dumps({"message": "WebSocket connected"}))

    async def disconnect(self, close_code):
        # Remove from the group on disconnect
        await self.channel_layer.group_discard("dashboard", self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.send(json.dumps({"echo": data}))

    async def push_event(self, event):
        # Handle events sent from emit/emit_sync
        await self.send(json.dumps(event['data']))

