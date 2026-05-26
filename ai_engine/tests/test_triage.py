import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from unittest.mock import patch

User = get_user_model()

@pytest.fixture
def auth_client():
    client = APIClient()
    user = User.objects.create_user(username='testpatient', password='password123', email='test@test.com')
    client.force_authenticate(user=user)
    return client

@pytest.mark.django_db
def test_triage_missing_symptoms(auth_client):
    url = reverse('ai_engine:triage')
    response = auth_client.post(url, {}, format='json')
    assert response.status_code == 400
    assert 'Symptoms required' in response.data['error']

@pytest.mark.django_db
@patch('ai_engine.clients.gemini_client.gemini_client.generate_json')
def test_triage_fallback(mock_generate, auth_client):
    # Simulate gemini failure
    mock_generate.side_effect = Exception("API Down")
    
    url = reverse('ai_engine:triage')
    response = auth_client.post(url, {'symptoms': 'headache and fever'}, format='json')
    
    assert response.status_code == 200
    assert response.data['urgency'] == 'LOW'
    assert 'keywords matching' in response.data['recommendation']
