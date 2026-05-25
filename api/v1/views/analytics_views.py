from rest_framework import viewsets, views, status, permissions
from rest_framework.response import Response
from django.db.models import Count, Sum, Avg
from drf_spectacular.utils import extend_schema
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from appointments.models import Appointment
from accounts.models import CustomUser
from billing.models import Transaction
from analytics.models import AIProcessingMetrics
from analytics.serializers import DashboardAnalyticsSerializer
from api.v1.permissions import IsAdminRole

class AnalyticsOverviewView(views.APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    @extend_schema(responses=DashboardAnalyticsSerializer)
    @method_decorator(cache_page(60 * 15)) # Cache for 15 mins
    def get(self, request):
        total_appointments = Appointment.objects.count()
        patients = CustomUser.objects.filter(role='patient').count()
        doctors = CustomUser.objects.filter(role='doctor').count()
        revenue = Transaction.objects.filter(payment_status='success').aggregate(Sum('amount'))['amount__sum'] or 0.0
        
        # OCR metrics
        total_ocr = AIProcessingMetrics.objects.count()
        ocr_success = AIProcessingMetrics.objects.filter(is_success=True).count()
        ocr_success_rate = (ocr_success / total_ocr * 100) if total_ocr > 0 else 0.0
        
        # Appointments by status
        status_counts = Appointment.objects.values('status').annotate(count=Count('status'))
        status_dict = {item['status']: item['count'] for item in status_counts}

        data = {
            "total_appointments": total_appointments,
            "active_patients": patients,
            "active_doctors": doctors,
            "total_revenue": float(revenue),
            "ocr_success_rate": round(ocr_success_rate, 2),
            "appointments_by_status": status_dict
        }
        
        serializer = DashboardAnalyticsSerializer(data=data)
        serializer.is_valid()
        return Response(serializer.validated_data)
