import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get('user')
        
        if not self.user or self.user.is_anonymous:
            logger.warning("Rejected unauthenticated websocket connection.")
            await self.close(code=4003)
            return
            
        self.group_name = f"user_{self.user.id}"
        
        # Join user-specific group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        logger.info(f"WebSocket connected for user: {self.user.username} (Group: {self.group_name})")

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            logger.info(f"WebSocket disconnected for user: {self.user.username}")

    # Receive message from WebSocket (from frontend)
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get('action')
            if action == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'message': 'pong'
                }))
        except Exception as e:
            logger.error(f"Error receiving websocket message: {e}")

    # Receive message from room group (from backend)
    async def send_notification(self, event):
        payload = event['payload']
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'payload': payload
        }))
