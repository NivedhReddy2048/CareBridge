from django.db import models
from django.conf import settings
from appointments.models import Appointment, Doctor

class MedicalReport(models.Model):
    # 1. Links (All set to NULL=True to bypass migration errors)
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='medical_report', null=True, blank=True)
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='medical_reports', null=True, blank=True)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='authored_reports', null=True, blank=True)
    
    # 2. Clinical Data (With DEFAULTS to bypass errors)
    diagnosis = models.CharField(max_length=255, default="Pending Diagnosis", help_text="Main condition")
    symptoms = models.TextField(default="No symptoms recorded", help_text="Patient symptoms")
    medications = models.TextField(default="No medications prescribed", help_text="Prescribed medicines")
    
    # 3. Optional Fields
    lab_tests = models.TextField(blank=True, null=True, help_text="Required tests (optional)")
    doctor_notes = models.TextField(blank=True, null=True, help_text="Additional advice")
    
    # 4. File Attachment
    attachment = models.FileField(upload_to='reports/', blank=True, null=True, help_text="Upload Lab PDF or X-Ray")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        # Safety check in case patient is None during migration
        p_name = self.patient.username if self.patient else "Unknown Patient"
        return f"Report: {p_name} - {self.diagnosis}"

class MalwareScanLog(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('CLEAN', 'Clean'),
        ('INFECTED', 'Infected'),
        ('FAILED', 'Failed')
    )
    ehr_record = models.ForeignKey('ehr.EHRRecord', on_delete=models.CASCADE, related_name='malware_scans', null=True, blank=True)
    # Note: Renamed from medical_report to ehr_record to match the actual upload flow in EHRViewSet.
    filename = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    scan_provider = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Scan {self.filename} - {self.status}"