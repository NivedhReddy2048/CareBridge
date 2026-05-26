import pytest
from unittest.mock import patch
from ai_orchestration.tasks import process_consultation_intelligence
from ai_orchestration.models import AIProcessingJob
from telemedicine.models import ConsultationSession
from django.contrib.auth import get_user_model
from appointments.models import Appointment, Doctor
from django.utils import timezone
from celery.exceptions import Retry

User = get_user_model()

@pytest.fixture
def session_fixture():
    patient = User.objects.create_user(username='patient_rel', password='pw', role='PATIENT')
    doc_user = User.objects.create_user(username='doc_rel', password='pw', role='DOCTOR')
    doctor = Doctor.objects.create(user=doc_user, specialization='General')
    
    appointment = Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        date=timezone.now().date(),
        time=timezone.now().time(),
        status='confirmed'
    )
    
    session = ConsultationSession.objects.create(
        appointment=appointment,
        scheduled_start=timezone.now()
    )
    
    return session, patient

@pytest.mark.django_db
@patch('ai_orchestration.tasks.ClinicalIntelligenceService.analyze_consultation_events')
def test_ai_task_redis_celery_unavailable_simulation(mock_analyze, session_fixture):
    session, patient = session_fixture
    
    # Simulate a broker disconnect or Gemini timeout
    mock_analyze.side_effect = Exception("Connection Timeout")
    
    with patch('ai_orchestration.tasks.process_consultation_intelligence.retry', side_effect=Retry):
        with pytest.raises(Retry):
            process_consultation_intelligence(session.id)
            
    # Assert that even though inference failed, the system recorded the failure gracefully
    # rather than crashing the websocket loop
    job = AIProcessingJob.objects.get(session=session)
    assert job.status == 'RETRYING'
