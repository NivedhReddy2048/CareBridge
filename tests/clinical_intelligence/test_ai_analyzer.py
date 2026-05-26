import pytest
from unittest.mock import patch
from django.contrib.auth import get_user_model
from telemedicine.models import ConsultationSession, ConsultationEvent
from appointments.models import Appointment, Doctor
from clinical_intelligence.services.ai_analyzer import ClinicalIntelligenceService
from clinical_intelligence.models import ClinicalInsightEvent

User = get_user_model()

@pytest.fixture
def session_with_chat():
    from django.utils import timezone
    patient = User.objects.create_user(username='patient2', password='pw', role='PATIENT')
    doc_user = User.objects.create_user(username='doc2', password='pw', role='DOCTOR')
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
    
    ConsultationEvent.objects.create(
        session=session,
        sender=patient,
        event_type='CHAT',
        payload={'text': 'I have chest pain and shortness of breath.'}
    )
    
    return session, patient

@pytest.mark.django_db
@patch('clinical_intelligence.services.ai_analyzer.gemini_client.generate_json')
def test_clinical_intelligence_analysis(mock_generate, session_with_chat):
    session, patient = session_with_chat
    
    mock_generate.return_value = {
        "symptoms_extracted": ["chest pain", "shortness of breath"],
        "risks_identified": ["Cardiac event"],
        "summary": "Patient reporting severe chest pain.",
        "emergency_escalation": True
    }
    
    result = ClinicalIntelligenceService.analyze_consultation_events(session.id, patient)
    
    assert result is not None
    assert result['emergency_escalation'] is True
    
    # Check if ClinicalInsightEvent was created
    insights = ClinicalInsightEvent.objects.filter(patient=patient)
    assert insights.count() == 2 # 1 for emergency, 1 for risk

@pytest.mark.django_db
@patch('clinical_intelligence.services.ai_analyzer.gemini_client.generate_json', side_effect=Exception("API Down"))
def test_clinical_intelligence_fallback(mock_generate, session_with_chat):
    session, patient = session_with_chat
    
    # Should degrade gracefully without throwing
    result = ClinicalIntelligenceService.analyze_consultation_events(session.id, patient)
    
    assert result is None
