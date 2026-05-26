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

class HealthCheckView(APIView):
    permission_classes = [] # Public endpoint for load balancers
    authentication_classes = []
    serializer_class = HealthCheckSerializer

    @extend_schema(responses={200: HealthCheckSerializer})
    def get(self, request):
        return Response({"status": "ok"}, status=200)
