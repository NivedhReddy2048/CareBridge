from rest_framework import serializers
from .models import AITriageEstimate, AIProcessingMetrics, SystemHealthLog

class AITriageEstimateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AITriageEstimate
        fields = '__all__'

class AIProcessingMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIProcessingMetrics
        fields = '__all__'

class DashboardAnalyticsSerializer(serializers.Serializer):
    total_appointments = serializers.IntegerField()
    active_patients = serializers.IntegerField()
    active_doctors = serializers.IntegerField()
    total_revenue = serializers.FloatField()
    ocr_success_rate = serializers.FloatField()
    appointments_by_status = serializers.DictField()
