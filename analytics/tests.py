import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import CustomUser

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def create_admin_user(db):
    def make_admin(**kwargs):
        return CustomUser.objects.create_superuser(username='admin1', email='admin@test.com', password='Admin@123', **kwargs)
    return make_admin

@pytest.fixture
def create_patient_user(db):
    def make_patient(**kwargs):
        return CustomUser.objects.create_user(username='patient1', role='patient', password='Patient@123', **kwargs)
    return make_patient

@pytest.mark.django_db
def test_analytics_overview_unauthorized(api_client, create_patient_user):
    create_patient_user()
    url = reverse('token_obtain_pair')
    token_response = api_client.post(url, {'username': 'patient1', 'password': 'Patient@123'})
    access_token = token_response.data['access']
    
    api_client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)
    
    url_analytics = reverse('api-analytics-overview')
    response = api_client.get(url_analytics)
    
    # Patient should be forbidden
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
def test_analytics_overview_authorized(api_client, create_admin_user):
    create_admin_user()
    url = reverse('token_obtain_pair')
    token_response = api_client.post(url, {'username': 'admin1', 'password': 'Admin@123'})
    access_token = token_response.data['access']
    
    api_client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)
    
    url_analytics = reverse('api-analytics-overview')
    response = api_client.get(url_analytics)
    
    # Admin should be allowed
    assert response.status_code == status.HTTP_200_OK
    assert 'total_appointments' in response.data
    assert 'ocr_success_rate' in response.data
