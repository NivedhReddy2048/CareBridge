import os
import django
from django.test import Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from accounts.models import CustomUser
from appointments.models import Doctor, Appointment
from billing.models import Transaction, Invoice
from ehr.models import EHRRecord, DocumentAttachment, AppointmentEHRLink
from intelligence.models import AIAnalysisResult

print("--- E2E TEST: EHR INTELLIGENCE PIPELINE ---")

client = Client()

# 1. SETUP & LOGIN
print("\n[1] SETUP & LOGGING IN")
patient = CustomUser.objects.filter(username='patient_test_01').first()
if not patient:
    patient = CustomUser.objects.create_user(username='patient_test_01', password='Patient@123', role='patient')
    print("Created test patient.")
client.login(username='patient_test_01', password='Patient@123')
doctor = Doctor.objects.first()

# 2. BOOKING WITH EHR UPLOAD
print("\n[2] BOOKING APPOINTMENT WITH EHR UPLOAD")
mock_pdf = SimpleUploadedFile("test_report.pdf", b"file_content", content_type="application/pdf")

response = client.post(reverse('book_appointment'), {
    'doctor': doctor.id,
    'date': '2026-06-15',
    'time': '10:00',
    'reason': 'E2E Test EHR Integration',
    'ehr_file': mock_pdf
}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

if response.status_code == 200:
    data = response.json()
    appointment_id = data.get('appointment_id')
    print(f"-> Appointment Created: {appointment_id}")
    
    appointment = Appointment.objects.get(id=appointment_id)
    
    # 3. VERIFY EHR LINKAGE
    link = AppointmentEHRLink.objects.filter(appointment=appointment).first()
    if link:
        print(f"-> SUCCESS: EHR Record Linked to Appointment! (Record ID: {link.ehr_record.id})")
        attachment = link.ehr_record.attachments.first()
        
        # 4. VERIFY AI ANALYSIS GENERATION
        # Since CELERY_TASK_ALWAYS_EAGER = True, this should be synchronous!
        ai_result = AIAnalysisResult.objects.filter(document=attachment).first()
        if ai_result:
            print("-> SUCCESS: AI Analysis Generated Synchronously!")
            print(f"   Summary: {ai_result.ai_summary['summary']}")
            print(f"   Conditions: {ai_result.identified_conditions}")
        else:
            print("-> FAILED: AI Analysis not generated.")
            
    else:
        print("-> FAILED: No EHR Record linked.")
        
else:
    print(f"-> Failed to book appointment. Status: {response.status_code}")

# 5. PATIENT DASHBOARD ACCESS
print("\n[5] VERIFYING PATIENT DASHBOARD ACCESS")
response = client.get(reverse('ehr_dashboard'))
if response.status_code == 200 and 'test_report.pdf' in str(response.content) or 'Record for Visit' in str(response.content):
    print("-> SUCCESS: EHR Dashboard loads and shows record.")
else:
    print("-> FAILED: EHR Dashboard did not render correctly.")
    
# 6. DOCTOR DASHBOARD ACCESS
print("\n[6] VERIFYING DOCTOR DASHBOARD ACCESS")
client.login(username=doctor.user.username, password='Doctor@123')
response = client.get(reverse('doctor_dashboard'))
if response.status_code == 200:
    print("-> SUCCESS: Doctor Dashboard loads.")
    if 'AI Patient Brief' in str(response.content):
        print("-> SUCCESS: AI Brief Sidebar button injected into Doctor Dashboard.")
    else:
        print("-> FAILED: AI Brief Sidebar button missing.")

print("\n--- E2E TEST COMPLETED ---")
