import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ConsultationSession, ConsultationParticipant, ConsultationEvent

logger = logging.getLogger(__name__)

class TelemedicineConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get('user')
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        
        if not self.user or self.user.is_anonymous:
            logger.warning("Rejected unauthenticated telemedicine connection.")
            await self.close(code=4003)
            return

        is_participant = await self.check_participant(self.room_id, self.user)
        if not is_participant:
            logger.warning(f"User {self.user.username} denied access to room {self.room_id}.")
            await self.close(code=4003)
            return

        self.room_group_name = f"telemedicine_{self.room_id}"
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Broadcast join
        await self.save_event('JOIN', {'user_id': self.user.id, 'username': self.user.username})
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_message',
                'event_type': 'JOIN',
                'payload': {'user_id': self.user.id, 'username': self.user.username}
            }
        )

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            # Broadcast leave
            await self.save_event('LEAVE', {'user_id': self.user.id, 'username': self.user.username})
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_message',
                    'event_type': 'LEAVE',
                    'payload': {'user_id': self.user.id, 'username': self.user.username}
                }
            )
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            event_type = data.get('type')
            payload = data.get('payload', {})
            
            # Save the event if it's chat or signal
            if event_type in ['CHAT', 'SIGNAL']:
                await self.save_event(event_type, payload)
                
            if event_type == 'CHAT':
                # Fire async Celery task to process intelligence without blocking websocket
                from ai_orchestration.tasks import process_consultation_intelligence
                # In async context, we must use sync_to_async to call delay
                from asgiref.sync import sync_to_async
                await sync_to_async(process_consultation_intelligence.delay)(self.room_id)
            
            # Broadcast to everyone else in the room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_message',
                    'event_type': event_type,
                    'payload': payload,
                    'sender_id': self.user.id
                }
            )
        except Exception as e:
            logger.error(f"Error in telemedicine consumer: {e}")

    async def broadcast_message(self, event):
        event_type = event.get('event_type')
        payload = event.get('payload')
        sender_id = event.get('sender_id')
        
        # We might not want to echo signals back to the sender
        if event_type == 'SIGNAL' and sender_id == self.user.id:
            return
            
        await self.send(text_data=json.dumps({
            'type': event_type,
            'payload': payload,
            'sender_id': sender_id
        }))

    @database_sync_to_async
    def check_participant(self, room_id, user):
        try:
            return ConsultationParticipant.objects.filter(session_id=room_id, user=user).exists()
        except Exception:
            return False

    @database_sync_to_async
    def save_event(self, event_type, payload):
        try:
            ConsultationEvent.objects.create(
                session_id=self.room_id,
                sender=self.user,
                event_type=event_type,
                payload=payload
            )
        except Exception as e:
            logger.error(f"Failed to save event: {e}")
