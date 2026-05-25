from django.db import models
from django.conf import settings
from appointments.models import Appointment

class EHRRecord(models.Model):
    RECORD_TYPES = [
        ('lab_report', 'Lab Report'),
        ('prescription', 'Prescription'),
        ('scan', 'Medical Scan'),
        ('blood_report', 'Blood Report'),
        ('general', 'General Record'),
    ]

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='ehr_records',
        limit_choices_to={'role': 'patient'}
    )
    title = models.CharField(max_length=255)
    record_type = models.CharField(max_length=50, choices=RECORD_TYPES, default='general')
    date_of_record = models.DateField()
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_of_record', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.patient.username}"

class DocumentAttachment(models.Model):
    ehr_record = models.ForeignKey(EHRRecord, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='ehr_documents/') # Fallback local storage, later S3
    file_type = models.CharField(max_length=50, blank=True, null=True) # e.g. 'application/pdf', 'image/png'
    file_hash = models.CharField(max_length=255, blank=True, null=True) # For malware/duplicate checking
    is_scanned = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for {self.ehr_record.title}"

class AppointmentEHRLink(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='ehr_links')
    ehr_record = models.ForeignKey(EHRRecord, on_delete=models.CASCADE, related_name='appointment_links')
    doctor_permission_granted = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('appointment', 'ehr_record')

    def __str__(self):
        return f"Link: {self.appointment.id} -> {self.ehr_record.id}"

class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='ehr_audit_logs')
    ehr_record = models.ForeignKey(EHRRecord, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255) # e.g. "VIEWED_RECORD", "DOWNLOADED_ATTACHMENT"
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username if self.user else 'System'} - {self.action} at {self.timestamp}"
