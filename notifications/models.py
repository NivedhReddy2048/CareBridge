from django.db import models
from django.conf import settings

class Notification(models.Model):
    TYPES = (
        ('APPOINTMENT_BOOKED', 'Appointment Booked'),
        ('APPOINTMENT_CONFIRMED', 'Appointment Confirmed'),
        ('PAYMENT_SUCCESS', 'Payment Success'),
        ('AI_ANALYSIS_READY', 'AI Analysis Ready'),
        ('DOCTOR_MESSAGE', 'Doctor Message'),
        ('PRESCRIPTION_READY', 'Prescription Ready'),
    )
    
    PRIORITIES = (
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='realtime_notifications')
    type = models.CharField(max_length=50, choices=TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITIES, default='normal')
    
    link = models.CharField(max_length=255, blank=True, null=True, help_text="Optional URL to redirect when clicked")
    
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.user.username} - {self.type} - {self.title}"

class NotificationPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_preferences')
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Prefs for {self.user.username}"

class RealTimeEventLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Event {self.event_type} at {self.created_at}"
