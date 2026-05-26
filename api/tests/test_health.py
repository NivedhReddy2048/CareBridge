import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch

@pytest.mark.django_db
def test_health_check_ok():
    client = APIClient()
    url = reverse('api-health-check')
    
    response = client.get(url, HTTP_ACCEPT='application/json')
    assert response.status_code == 200
    assert response.data['status'] == 'ok'
