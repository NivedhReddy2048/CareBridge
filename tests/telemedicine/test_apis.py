import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from appointments.models import Appointment, Doctor
from telemedicine.models import ConsultationSession

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def test_users():
    patient = User.objects.create_user(username='patient1', password='pw', role='PATIENT')
    doc_user = User.objects.create_user(username='doc1', password='pw', role='DOCTOR')
    doctor = Doctor.objects.create(user=doc_user, specialization='General')
    return patient, doctor

@pytest.fixture
def appointment(test_users):
    patient, doctor = test_users
    from django.utils import timezone
    return Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        date=timezone.now().date(),
        time=timezone.now().time(),
        status='confirmed'
    )

from unittest.mock import patch

@pytest.mark.django_db
@patch('django.test.signals.template_rendered.send')
def test_create_consultation(mock_send, api_client, appointment, test_users):
    patient, _ = test_users
    api_client.force_authenticate(user=patient)
    
    url = reverse('telemedicine:create_consultation')
    response = api_client.post(url, {'appointment_id': appointment.id}, format='json')
    
    assert response.status_code == 201
    assert 'id' in response.data
    assert response.data['status'] == 'SCHEDULED'

@pytest.mark.django_db
@patch('django.test.signals.template_rendered.send')
def test_join_consultation(mock_send, api_client, appointment, test_users):
    patient, _ = test_users
    api_client.force_authenticate(user=patient)
    
    # Create first
    from django.utils import timezone
    session = ConsultationSession.objects.create(
        appointment=appointment,
        scheduled_start=timezone.now()
    )
    
    url = reverse('telemedicine:join_consultation', kwargs={'pk': session.id})
    response = api_client.post(url, {'role': 'PATIENT'}, format='json')
    
    assert response.status_code == 200
    assert response.data['status'] == 'WAITING'
    
@pytest.mark.django_db
@patch('django.test.signals.template_rendered.send')
def test_end_consultation_unauthorized(mock_send, api_client, appointment, test_users):
    patient, _ = test_users
    
    # Someone else
    other_user = User.objects.create_user(username='other', password='pw')
    api_client.force_authenticate(user=other_user)
    
    from django.utils import timezone
    session = ConsultationSession.objects.create(
        appointment=appointment,
        scheduled_start=timezone.now()
    )
    
    url = reverse('telemedicine:end_consultation', kwargs={'pk': session.id})
    response = api_client.post(url, format='json')
    
    assert response.status_code == 403
