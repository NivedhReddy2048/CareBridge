from django.db import models
from django.conf import settings
from appointments.models import Appointment
from ehr.models import EHRRecord

class AIUsageLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    endpoint = models.CharField(max_length=255)
    tokens_used = models.IntegerField(default=0)
    latency_ms = models.IntegerField(default=0)
    fallback_triggered = models.BooleanField(default=False)
    status = models.CharField(max_length=50, default='SUCCESS') # SUCCESS, ERROR, FALLBACK
    model_name = models.CharField(max_length=100, default='gemini-2.5-flash')
    created_at = models.DateTimeField(auto_now_add=True)

class AIAuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    raw_prompt = models.TextField()
    cleaned_prompt = models.TextField()
    raw_response = models.TextField(blank=True, null=True)
    parsed_response = models.JSONField(blank=True, null=True)
    fallback_reason = models.TextField(blank=True, null=True)
    emergency_escalation = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

class AIConversation(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_conversations')
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class AIMessage(models.Model):
    conversation = models.ForeignKey(AIConversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=50) # 'user', 'model', 'system'
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

class AISummaryCache(models.Model):
    ehr_record = models.ForeignKey(EHRRecord, on_delete=models.CASCADE)
    summary = models.TextField()
    confidence = models.FloatField(default=0.0)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
