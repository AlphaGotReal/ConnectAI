# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Extract room name and group name
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        user = self.scope["user"]

        # Check if the user is authenticated
        if not user.is_authenticated:
            await self.close()
            return

        # Validate the room name format (e.g., "user1-user2")
        try:
            user1, user2 = self.room_name.split("-")
        except ValueError:
            await self.close()
            return

        # Check if the user is one of the participants
        if user.username not in [user1, user2]:
            await self.close()
            return

        # Add the user to the WebSocket group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Accept the WebSocket connection
        await self.accept()

    async def disconnect(self, close_code):
        # Remove the user from the WebSocket group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Parse the incoming WebSocket message
        data = json.loads(text_data)

        # Extract the message and sender
        message = data.get("message")
        sender = self.scope["user"].username

        # Broadcast the message to the group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "sender": sender,
            }
        )

    async def chat_message(self, event):
        # Send the message to WebSocket clients
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "sender": event["sender"],
        }))