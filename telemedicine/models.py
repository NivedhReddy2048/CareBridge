import uuid
from django.db import models
from django.conf import settings
from appointments.models import Appointment

class ConsultationSession(models.Model):
    STATUS_CHOICES = (
        ('SCHEDULED', 'Scheduled'),
        ('WAITING', 'Waiting'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='consultation_session')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    scheduled_start = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session {self.id} - {self.status}"

class ConsultationParticipant(models.Model):
    ROLE_CHOICES = (
        ('DOCTOR', 'Doctor'),
        ('PATIENT', 'Patient'),
        ('OBSERVER', 'Observer'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ConsultationSession, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='consultation_participations')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    joined_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    connection_quality = models.JSONField(default=dict, blank=True)
    
    class Meta:
        unique_together = ('session', 'user')

class ConsultationEvent(models.Model):
    EVENT_TYPES = (
        ('CHAT', 'Chat Message'),
        ('SIGNAL', 'WebRTC Signal'),
        ('JOIN', 'Participant Joined'),
        ('LEAVE', 'Participant Left'),
        ('SYSTEM', 'System Event'),
        ('AI_UPDATE', 'AI Intelligence Update'),
        ('EMERGENCY', 'Emergency Escalation'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ConsultationSession, on_delete=models.CASCADE, related_name='events')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    payload = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)

class ConsultationRecordingMetadata(models.Model):
    session = models.OneToOneField(ConsultationSession, on_delete=models.CASCADE, related_name='recording_metadata')
    s3_path = models.CharField(max_length=512, blank=True, null=True)
    duration_seconds = models.IntegerField(default=0)
    file_size_bytes = models.BigIntegerField(default=0)
    is_processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class ConsultationAuditLog(models.Model):
    session = models.ForeignKey(ConsultationSession, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=255)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
