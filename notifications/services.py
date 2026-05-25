from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from notifications.models import Notification, RealTimeEventLog
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    def send_notification(user, n_type, title, message, priority='normal', link=None):
        """Creates a Notification object and pushes it over websockets."""
        notification = Notification.objects.create(
            user=user,
            type=n_type,
            title=title,
            message=message,
            priority=priority,
            link=link
        )
        
        channel_layer = get_channel_layer()
        if channel_layer:
            group_name = f"user_{user.id}"
            payload = {
                'id': notification.id,
                'type': notification.type,
                'title': notification.title,
                'message': notification.message,
                'priority': notification.priority,
                'link': notification.link,
                'created_at': notification.created_at.isoformat(),
            }
            
            try:
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        'type': 'send_notification',
                        'payload': payload
                    }
                )
                logger.info(f"Pushed notification via websocket to {group_name}")
            except Exception as e:
                logger.error(f"Failed to push notification to websocket: {e}")
                
            RealTimeEventLog.objects.create(
                user=user,
                event_type=n_type,
                payload=payload
            )
        return notification
