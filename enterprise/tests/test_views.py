import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
def test_enterprise_login_redirect(client):
    url = reverse('enterprise:dashboard')
    response = client.get(url)
    assert response.status_code == 302
    assert '/enterprise/login/' in response.url

from unittest.mock import patch

@pytest.mark.django_db
@patch('enterprise.views.render')
def test_enterprise_admin_access(mock_render, client):
    from django.http import HttpResponse
    mock_render.return_value = HttpResponse()
    admin = User.objects.create_superuser('admin', 'admin@test.com', 'pass')
    client.force_login(admin)
    url = reverse('enterprise:dashboard')
    response = client.get(url)
    assert response.status_code == 200

@pytest.mark.django_db
def test_enterprise_patient_blocked(client):
    patient = User.objects.create_user('patient', 'patient@test.com', 'pass')
    client.force_login(patient)
    url = reverse('enterprise:dashboard')
    response = client.get(url)
    assert response.status_code == 403
