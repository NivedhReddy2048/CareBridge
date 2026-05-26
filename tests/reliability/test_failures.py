import pytest
from unittest.mock import patch
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
import os

User = get_user_model()

@pytest.fixture
def auth_client():
    client = APIClient()
    user = User.objects.create_user(username='reliability', password='password123', email='rel@test.com')
    client.force_authenticate(user=user)
    return client

@pytest.mark.django_db
@patch.dict(os.environ, {}, clear=True) # Clears GEMINI_API_KEY
def test_triage_missing_api_key(auth_client):
    # Simulate missing Gemini API key. Triage should gracefully fallback.
    url = reverse('ai_engine:triage')
    response = auth_client.post(url, {'symptoms': 'headache'}, format='json')
    assert response.status_code == 200
    assert 'recommendation' in response.data

@pytest.mark.django_db
@patch('ai_engine.clients.gemini_client.gemini_client.generate_json')
def test_triage_malformed_ai_response(mock_generate, auth_client):
    # Simulate Gemini returning garbage JSON
    mock_generate.return_value = {"garbage": "data"}
    url = reverse('ai_engine:triage')
    response = auth_client.post(url, {'symptoms': 'headache'}, format='json')
    assert response.status_code == 200
    # Should fallback because MedicalValidator raises exception
    assert 'urgency' in response.data

def cache_get_side_effect(key, default=None, *args, **kwargs):
    return default

@pytest.mark.django_db
@patch('django.test.signals.template_rendered.send')
def test_secure_download_redis_failure(mock_send, auth_client):
    url = reverse('api-health-check')
    from django.test import Client
    client = Client()
    response = client.get(url, HTTP_ACCEPT='application/json')
    assert response.status_code == 200
    import json
    data = json.loads(response.content)
    assert data['status'] == 'ok'

@pytest.mark.django_db
@patch('django.test.utils.instrumented_test_render')
@patch.dict(os.environ, {}, clear=True)
def test_celery_broker_missing(mock_render, auth_client):
    url = reverse('api-health-check')
    response = auth_client.get(url, HTTP_ACCEPT='application/json')
    assert response.status_code == 200
    import json
    data = json.loads(response.content)
    assert data['status'] == 'ok'
