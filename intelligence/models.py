from django.db import models
from ehr.models import DocumentAttachment
from django.conf import settings

class AIAnalysisResult(models.Model):
    document = models.OneToOneField(DocumentAttachment, on_delete=models.CASCADE, related_name='ai_analysis')
    raw_extracted_text = models.TextField(blank=True, null=True)
    ai_summary = models.JSONField(blank=True, null=True, help_text="Structured summary of the document")
    identified_conditions = models.JSONField(blank=True, null=True, help_text="List of extracted conditions")
    extracted_medications = models.JSONField(blank=True, null=True, help_text="List of extracted medications")
    confidence_score = models.FloatField(default=0.0)
    processed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"AI Analysis for Doc {self.document.id}"

class PatientTimeline(models.Model):
    patient = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='timeline',
        limit_choices_to={'role': 'patient'}
    )
    latest_summary = models.JSONField(blank=True, null=True, help_text="Aggregate summary of the patient's entire history")
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Timeline for {self.patient.username}"
