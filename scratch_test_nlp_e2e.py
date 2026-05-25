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

print("--- E2E TEST: DYNAMIC NLP INTELLIGENCE PIPELINE ---")

client = Client()

patient = CustomUser.objects.filter(username='patient_test_01').first()
if not patient:
    patient = CustomUser.objects.create_user(username='patient_test_01', password='Patient@123', role='patient')
client.login(username='patient_test_01', password='Patient@123')
doctor = Doctor.objects.first()

print("\n[1] MOCKING A PDF WITH SPECIFIC SYMPTOMS")
# We will create a small PDF using reportlab to ensure pdfplumber extracts it.
from reportlab.pdfgen import canvas
pdf_path = "mri_shoulder.pdf"
c = canvas.Canvas(pdf_path)
c.drawString(100, 750, "Patient underwent MRI of the right joint.")
c.drawString(100, 730, "Findings show an anterior shoulder dislocation with some joint instability.")
c.drawString(100, 710, "Recommend orthopedic injury consult.")
c.drawString(100, 690, "Prescribed ibuprofen for pain management.")
c.save()

print("\n[2] UPLOADING MRI REPORT VIA BOOKING")
with open(pdf_path, "rb") as f:
    mock_pdf = SimpleUploadedFile(pdf_path, f.read(), content_type="application/pdf")
    response = client.post(reverse('book_appointment'), {
        'doctor': doctor.id,
        'date': '2026-06-16',
        'time': '11:00',
        'reason': 'Shoulder pain following fall',
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
        
        print(f"\n[3] AI ANALYSIS RESULTS FOR APPT {appointment_id}")
        print(f"RAW TEXT: {ai_result.raw_extracted_text}")
        print(f"SUMMARY: {ai_result.ai_summary['summary']}")
        print(f"CONDITIONS: {ai_result.identified_conditions}")
        print(f"MEDICATIONS: {ai_result.extracted_medications}")
        print(f"CONFIDENCE: {ai_result.confidence_score}")
        
        # ASSERTIONS
        assert "shoulder dislocation" in ai_result.identified_conditions, "Failed to extract shoulder dislocation"
        assert "joint instability" in ai_result.identified_conditions, "Failed to extract joint instability"
        assert "ibuprofen" in ai_result.extracted_medications, "Failed to extract ibuprofen"
        assert "fever" not in ai_result.identified_conditions, "Hallucinated 'fever' condition"
        print("\n-> SUCCESS: AI pipeline successfully extracted specific NLP conditions dynamically without hallucinating!")
        
    else:
        print("-> FAILED: No EHR Record linked.")
else:
    print(f"-> Failed to book appointment. Status: {response.status_code}")

# Cleanup
if os.path.exists(pdf_path):
    os.remove(pdf_path)
print("\n--- E2E TEST COMPLETED ---")
