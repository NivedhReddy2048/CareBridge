from django.db import models
from django.conf import settings
from ehr.models import EHRRecord

class PatientTimelineSummary(models.Model):
    """
    Caches expensive AI longitudinal aggregations for a patient.
    """
    patient = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='timeline_summary')
    ehr_record = models.OneToOneField(EHRRecord, on_delete=models.CASCADE, related_name='intelligence_summary')
    
    # Cached AI-generated insights
    symptom_progression = models.JSONField(default=list, blank=True)
    medication_history_analysis = models.JSONField(default=dict, blank=True)
    recurring_conditions = models.JSONField(default=list, blank=True)
    risk_trend_analysis = models.JSONField(default=dict, blank=True)
    ai_generated_summary = models.TextField(blank=True, null=True)
    
    last_computed = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Timeline Summary for {self.patient.username}"

class ClinicalInsightEvent(models.Model):
    """
    A specific event or insight flagged by the Clinical Intelligence engine.
    """
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='clinical_insights')
    insight_type = models.CharField(max_length=50) # e.g. 'RISK_ESCALATION', 'DRUG_INTERACTION', 'CHRONIC_PATTERN'
    description = models.TextField()
    confidence = models.FloatField(default=0.0)
    related_consultation = models.ForeignKey('telemedicine.ConsultationSession', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_acknowledged = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.insight_type} - {self.patient.username}"
