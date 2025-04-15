import json 
from channels.generic.websocket import AsyncWebsocketConsumer  
from channels.db import database_sync_to_async
from django.contrib.auth.models import User 
from django.utils import timezone  
from .models import Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        user = self.scope["user"]

        if not user.is_authenticated:
            await self.close()
            return

        try:
            user1, user2 = self.room_name.split("-")
        except ValueError:
            await self.close()
            return

        if user.username not in [user1, user2]:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Send chat history when a user connects
        await self.send_chat_history()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message')
        sender_username = self.scope["user"].username

        try:
            user1, user2 = self.room_name.split('-')
            receiver_username = user1 if sender_username == user2 else user2
        except ValueError:
            return

        await self.save_message(sender_username, receiver_username, message, self.room_name)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender_username,
                'timestamp': timezone.now().isoformat()
            }
        )

    @database_sync_to_async
    def save_message(self, sender_username, receiver_username, message, room_name):
        sender = User.objects.get(username=sender_username)
        receiver = User.objects.get(username=receiver_username)

        Message.objects.create(
            sender=sender,
            receiver=receiver,
            messages=message,
            room_name=room_name,
            timestamp=timezone.now()
        )

    @database_sync_to_async
    def get_chat_history(self):
        return list(Message.objects.filter(room_name=self.room_name)
                          .order_by('timestamp')
                          .select_related('sender'))

    async def send_chat_history(self):
        messages = await self.get_chat_history()
        for message in messages:
            await self.send(text_data=json.dumps({
                "message": message.messages,
                "sender": message.sender.username,
                "timestamp": message.timestamp.isoformat()
            }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "sender": event["sender"],
            "timestamp": event["timestamp"]
        }))