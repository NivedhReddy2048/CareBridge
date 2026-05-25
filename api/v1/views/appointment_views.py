from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.utils import timezone

from appointments.models import Appointment, Doctor
from api.v1.serializers.appointment_serializers import AppointmentSerializer, AppointmentBookingSerializer, DoctorSerializer
from api.v1.permissions import IsPatient, IsDoctor

class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Appointment.objects.none()
            
        if getattr(user, 'role', None) == 'patient':
            return Appointment.objects.filter(patient=user)
        elif getattr(user, 'role', None) == 'doctor':
            return Appointment.objects.filter(doctor__user=user)
        return Appointment.objects.all()

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser], permission_classes=[IsPatient])
    def book(self, request):
        serializer = AppointmentBookingSerializer(data=request.data)
        if serializer.is_valid():
            doctor_id = serializer.validated_data['doctor_id']
            date = serializer.validated_data['date']
            time = serializer.validated_data['time']
            reason = serializer.validated_data['reason']
            ehr_file = serializer.validated_data.get('ehr_file')

            if Appointment.objects.filter(doctor_id=doctor_id, date=date, time=time, status='confirmed').exists():
                return Response({"error": "Slot already booked."}, status=status.HTTP_409_CONFLICT)

            doctor = get_object_or_404(Doctor, id=doctor_id)
            appointment = Appointment.objects.create(
                patient=request.user, 
                doctor=doctor, 
                date=date, 
                time=time, 
                reason=reason, 
                status='pending'
            )

            # Phase 6: AI Triage Estimation
            try:
                from analytics.services.triage_service import TriageEngine
                TriageEngine.estimate_triage(symptoms=reason, patient=request.user, appointment=appointment)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Failed to generate triage estimate: {e}")

            if ehr_file:
                from ehr.models import EHRRecord, DocumentAttachment, AppointmentEHRLink, AuditLog
                record = EHRRecord.objects.create(
                    patient=request.user,
                    title=f"Record for Visit {date}",
                    record_type="general",
                    date_of_record=date,
                    notes=reason
                )
                DocumentAttachment.objects.create(
                    ehr_record=record,
                    file=ehr_file
                )
                AppointmentEHRLink.objects.create(
                    appointment=appointment,
                    ehr_record=record,
                    doctor_permission_granted=True
                )
                AuditLog.objects.create(
                    user=request.user, # The original monolithic codebase uses 'user' instead of 'accessed_by'
                    ehr_record=record,
                    action="UPLOADED_DURING_BOOKING",
                    ip_address=request.META.get('REMOTE_ADDR')
                )

            return Response({"status": "success", "appointment_id": appointment.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DoctorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAuthenticated]
