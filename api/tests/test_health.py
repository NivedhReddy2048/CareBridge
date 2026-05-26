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
    assert response.data['status'] == 'healthy'
    assert response.data['services']['database'] == 'ok'

@pytest.mark.django_db
@patch('django.test.signals.template_rendered.send')
def test_health_check_db_down(mock_send):
    from django.test import Client
    client = Client()
    url = reverse('api-health-check')
    
    with patch('api.v1.views.system_views.connections') as mock_conn:
        mock_conn['default'].cursor.side_effect = Exception("DB Down")
        response = client.get(url, HTTP_ACCEPT='application/json')
        assert response.status_code == 503
        import json
        data = json.loads(response.content)
        assert data['status'] == 'unhealthy'
        assert data['services']['database'] == 'down'
