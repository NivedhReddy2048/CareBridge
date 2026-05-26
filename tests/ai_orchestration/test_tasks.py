import pytest
from unittest.mock import patch
from ai_orchestration.tasks import process_consultation_intelligence
from ai_orchestration.models import AIProcessingJob, AIProcessingResult, AIInferenceEvent
from telemedicine.models import ConsultationSession, ConsultationEvent
from django.contrib.auth import get_user_model
from appointments.models import Appointment, Doctor
from django.utils import timezone

User = get_user_model()

@pytest.fixture
def session_fixture():
    patient = User.objects.create_user(username='patient_ai', password='pw', role='PATIENT')
    doc_user = User.objects.create_user(username='doc_ai', password='pw', role='DOCTOR')
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

from unittest.mock import patch, AsyncMock

@pytest.mark.django_db
@patch('ai_orchestration.tasks.ClinicalIntelligenceService.analyze_consultation_events')
@patch('ai_orchestration.tasks.get_channel_layer')
def test_process_consultation_intelligence_success(mock_channel_layer, mock_analyze, session_fixture):
    session, patient = session_fixture
    
    mock_channel_layer.return_value.group_send = AsyncMock()
    
    mock_analyze.return_value = {
        "symptoms_extracted": ["headache"],
        "risks_identified": [],
        "summary": "Patient has headache.",
        "emergency_escalation": False
    }
    
    # Run the celery task synchronously
    process_consultation_intelligence(session.id)
    
    # Assert job created and completed
    job = AIProcessingJob.objects.get(session=session)
    assert job.status == 'COMPLETED'
    
    # Assert result created
    result = AIProcessingResult.objects.get(job=job)
    assert result.tokens_used == 500
    
    # Assert events
    events = AIInferenceEvent.objects.filter(job=job)
    assert events.count() == 2 # START, SUCCESS

@pytest.mark.django_db
@patch('ai_orchestration.tasks.ClinicalIntelligenceService.analyze_consultation_events')
def test_process_consultation_intelligence_failure(mock_analyze, session_fixture):
    session, patient = session_fixture
    
    # Simulate a crash inside analyze
    mock_analyze.side_effect = Exception("API Timeout")
    
    # Must use pytest.raises to catch the retry exception
    from celery.exceptions import Retry
    with patch('ai_orchestration.tasks.process_consultation_intelligence.retry', side_effect=Retry):
        with pytest.raises(Retry):
            process_consultation_intelligence(session.id)
            
    # Assert job state
    job = AIProcessingJob.objects.get(session=session)
    assert job.status == 'RETRYING'
    
    # Assert failure event logged
    events = AIInferenceEvent.objects.filter(job=job, is_error=True)
    assert events.count() == 1
