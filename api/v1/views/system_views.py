from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import connections
from django.db.utils import OperationalError
from django.core.cache import cache
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
import os

class HealthCheckSerializer(serializers.Serializer):
    status = serializers.CharField()
    services = serializers.DictField()

class HealthCheckView(APIView):
    permission_classes = [] # Public endpoint for load balancers
    authentication_classes = []
    serializer_class = HealthCheckSerializer

    @extend_schema(responses={200: HealthCheckSerializer})
    def get(self, request):
        health_status = {
            "status": "healthy",
            "services": {}
        }
        
        # 1. Database Check
        db_conn = connections['default']
        try:
            c = db_conn.cursor()
            c.execute("SELECT 1")
            health_status["services"]["database"] = "ok"
        except Exception:
            health_status["services"]["database"] = "down"
            health_status["status"] = "unhealthy"

        # 2. Redis/Cache Check
        try:
            cache.set('health_check', 'ok', timeout=1)
            if cache.get('health_check') == 'ok':
                health_status["services"]["redis"] = "ok"
            else:
                raise Exception("Cache mismatch")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("Redis health check failed safely (degraded).")
            health_status["services"]["redis"] = "degraded"
            # We don't mark the whole system as unhealthy just because cache/redis is down
            # as DRF APIs and Django will still boot.
            
        # 3. Storage Backend
        try:
            from django.core.files.storage import default_storage
            # Just check if we can instantiate / access it
            name = default_storage.__class__.__name__
            health_status["services"]["storage"] = f"ok ({name})"
        except Exception:
            health_status["services"]["storage"] = "down"
            health_status["status"] = "unhealthy"
            
        # 4. Gemini API / AI Engine check
        api_key = os.environ.get('GEMINI_API_KEY')
        if api_key:
            health_status["services"]["ai_engine"] = "configured"
        else:
            health_status["services"]["ai_engine"] = "missing_key"
            # We don't mark as unhealthy just for AI, fallback exists
            
        # 5. Celery Check
        try:
            # We don't want to block, so just check broker URL presence
            broker_url = os.environ.get('REDIS_URL')
            if broker_url:
                health_status["services"]["celery_broker"] = "configured"
            else:
                health_status["services"]["celery_broker"] = "missing"
        except Exception:
            health_status["services"]["celery_broker"] = "down"
            health_status["status"] = "unhealthy"
            
        status_code = 200 if health_status["status"] == "healthy" else 503
        return Response(health_status, status=status_code)
