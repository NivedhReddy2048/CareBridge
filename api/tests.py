import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import CustomUser

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def create_patient_user(db):
    def make_patient(**kwargs):
        return CustomUser.objects.create_user(username='patient1', role='patient', password='Patient@123', **kwargs)
    return make_patient

@pytest.fixture
def create_doctor_user(db):
    def make_doctor(**kwargs):
        return CustomUser.objects.create_user(username='doctor1', role='doctor', password='Doctor@123', **kwargs)
    return make_doctor

@pytest.mark.django_db
def test_obtain_jwt_token(api_client, create_patient_user):
    create_patient_user()
    url = reverse('token_obtain_pair')
    response = api_client.post(url, {'username': 'patient1', 'password': 'Patient@123'})
    
    assert response.status_code == status.HTTP_200_OK
    assert 'access' in response.data
    assert 'refresh' in response.data

@pytest.mark.django_db
def test_unauthenticated_ehr_access(api_client):
    url = reverse('ehr-list')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_authenticated_ehr_access(api_client, create_patient_user):
    user = create_patient_user()
    url = reverse('token_obtain_pair')
    token_response = api_client.post(url, {'username': 'patient1', 'password': 'Patient@123'})
    access_token = token_response.data['access']
    
    api_client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)
    
    url_ehr = reverse('ehr-list')
    response = api_client.get(url_ehr)
    
    assert response.status_code == status.HTTP_200_OK
