import os
import django
from django.test import Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from accounts.models import CustomUser
from appointments.models import Doctor, Appointment
from ehr.models import EHRRecord, DocumentAttachment, AppointmentEHRLink
from intelligence.models import AIAnalysisResult

print("--- E2E TEST: MOCK SCANNED PDF FALLBACK ---")

client = Client()
patient = CustomUser.objects.filter(username='patient_test_01').first()
client.login(username='patient_test_01', password='Patient@123')
doctor = Doctor.objects.first()

print("\n[1] MOCKING A SCANNED PDF WITH VERY LITTLE TEXT (<50 chars)")
from reportlab.pdfgen import canvas
pdf_path = "scanned_mock.pdf"
c = canvas.Canvas(pdf_path)
c.drawString(100, 750, "Img") # Only 3 characters, so pdfplumber won't extract > 50 chars
c.save()

print("\n[2] UPLOADING SCANNED PDF")
with open(pdf_path, "rb") as f:
    mock_pdf = SimpleUploadedFile(pdf_path, f.read(), content_type="application/pdf")
    response = client.post(reverse('book_appointment'), {
        'doctor': doctor.id,
        'date': '2026-06-16',
        'time': '12:00',
        'reason': 'Testing scanned PDF fallback',
        'ehr_file': mock_pdf
    }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

if response.status_code == 200:
    data = response.json()
    appointment_id = data.get('appointment_id')
    appointment = Appointment.objects.get(id=appointment_id)
    
    link = AppointmentEHRLink.objects.filter(appointment=appointment).first()
    if link:
        attachment = link.ehr_record.attachments.first()
        ai_result = AIAnalysisResult.objects.filter(document=attachment).first()
        
        print(f"\n[3] AI ANALYSIS RESULTS")
        print(f"RAW TEXT: {ai_result.raw_extracted_text}")
        print(f"SUMMARY: {ai_result.ai_summary['summary']}")
        print(f"EXTRACTION METHOD: {ai_result.ai_summary.get('extraction_method')}")
        
        assert "Scanned PDF OCR requires Poppler support" in ai_result.raw_extracted_text, "Fallback logic failed to detect scanned PDF"
        print("\n-> SUCCESS: Scanned PDF fallback logic worked perfectly!")
        
    else:
        print("-> FAILED: No EHR Record linked.")
else:
    print(f"-> Failed to book appointment. Status: {response.status_code}")

if os.path.exists(pdf_path):
    os.remove(pdf_path)
print("\n--- E2E TEST COMPLETED ---")
