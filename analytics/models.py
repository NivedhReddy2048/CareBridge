from django.db import models
from django.conf import settings
from ehr.models import DocumentAttachment

class SystemHealthLog(models.Model):
    component = models.CharField(max_length=100) # e.g., 'Celery', 'WebSocket', 'API'
    status = models.CharField(max_length=50) # 'UP', 'DOWN', 'DEGRADED'
    details = models.JSONField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.component} - {self.status} at {self.timestamp}"

class ErrorEventLog(models.Model):
    source = models.CharField(max_length=100)
    error_type = models.CharField(max_length=100)
    error_message = models.TextField()
    stack_trace = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

class AIProcessingMetrics(models.Model):
    document = models.ForeignKey(DocumentAttachment, on_delete=models.SET_NULL, null=True, blank=True)
    task_id = models.CharField(max_length=255, blank=True, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_seconds = models.FloatField()
    ocr_method = models.CharField(max_length=50) # 'PDF_TEXT', 'OCR_IMAGE', 'FAILED'
    is_success = models.BooleanField(default=True, db_index=True)
    confidence_score = models.FloatField(default=0.0)

    class Meta:
        indexes = [
            models.Index(fields=['start_time']),
        ]

    def __str__(self):
        return f"AI Task {self.task_id} - Duration: {self.duration_seconds}s"

class WebSocketConnectionMetrics(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    connected_at = models.DateTimeField(db_index=True)
    disconnected_at = models.DateTimeField(blank=True, null=True)
    duration_seconds = models.FloatField(blank=True, null=True)
    close_code = models.IntegerField(blank=True, null=True)

class AITriageEstimate(models.Model):
    TRIAGE_LEVELS = (
        ('LOW', 'Low - Routine'),
        ('MEDIUM', 'Medium - Urgent'),
        ('HIGH', 'High - Emergency'),
        ('CRITICAL', 'Critical - Immediate Response'),
    )
    appointment = models.OneToOneField('appointments.Appointment', on_delete=models.CASCADE, related_name='triage_estimate', null=True, blank=True)
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    symptoms = models.TextField()
    urgency_level = models.CharField(max_length=20, choices=TRIAGE_LEVELS)
    recommended_department = models.CharField(max_length=100)
    confidence_score = models.FloatField(default=0.0)
    reasoning = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Triage {self.urgency_level} - {self.recommended_department} ({self.patient.username})"
