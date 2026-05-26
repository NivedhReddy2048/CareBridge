import uuid
from django.db import models
from telemedicine.models import ConsultationSession
from django.conf import settings

class AIProcessingJob(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('RETRYING', 'Retrying'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ConsultationSession, on_delete=models.CASCADE, related_name='ai_jobs')
    job_type = models.CharField(max_length=50) # e.g., 'TRANSCRIPT_SUMMARY', 'RISK_ANALYSIS'
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payload = models.JSONField(default=dict, blank=True)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class AIProcessingResult(models.Model):
    job = models.OneToOneField(AIProcessingJob, on_delete=models.CASCADE, related_name='result')
    result_payload = models.JSONField(default=dict)
    tokens_used = models.IntegerField(default=0)
    latency_ms = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

class ConsultationTranscriptChunk(models.Model):
    session = models.ForeignKey(ConsultationSession, on_delete=models.CASCADE, related_name='transcript_chunks')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    text = models.TextField()
    is_processed = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

class AIInferenceEvent(models.Model):
    job = models.ForeignKey(AIProcessingJob, on_delete=models.CASCADE, related_name='inference_events', null=True, blank=True)
    event_type = models.CharField(max_length=50)
    message = models.TextField()
    is_error = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

class AIQueueMetric(models.Model):
    queue_name = models.CharField(max_length=50)
    backlog_size = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
