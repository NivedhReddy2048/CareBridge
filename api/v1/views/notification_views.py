from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from notifications.models import Notification
from notifications.serializers import NotificationSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = getattr(self.request, 'user', None)
        if user and user.is_authenticated:
            return Notification.objects.filter(user=user, is_deleted=False)
        return Notification.objects.none()

    @action(detail=True, methods=['post'])
    def read(self, request, pk=None):
        """Mark a specific notification as read."""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({"status": "success"})

    @action(detail=False, methods=['post'], url_path='read-all')
    def read_all(self, request):
        """Mark all notifications as read."""
        self.get_queryset().update(is_read=True)
        return Response({"status": "success"})
