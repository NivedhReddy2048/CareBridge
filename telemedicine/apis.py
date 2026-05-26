from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from django.utils import timezone
from .models import ConsultationSession, ConsultationParticipant, ConsultationEvent
from .serializers import (
    ConsultationSessionSerializer, 
    CreateConsultationRequestSerializer,
    JoinConsultationRequestSerializer,
    ConsultationEventSerializer
)
from appointments.models import Appointment

@extend_schema(
    request=CreateConsultationRequestSerializer,
    responses={201: ConsultationSessionSerializer},
    tags=['Telemedicine']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_consultation(request):
    """Create a new consultation session for an appointment."""
    serializer = CreateConsultationRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        appointment = Appointment.objects.get(id=serializer.validated_data['appointment_id'])
    except Appointment.DoesNotExist:
        return Response({"error": "Appointment not found"}, status=status.HTTP_404_NOT_FOUND)
        
    # Check if user is authorized (doctor or patient)
    if request.user != appointment.patient and request.user != appointment.doctor.user:
        return Response({"error": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)
        
    from django.utils import timezone
    import datetime
    
    dt = datetime.datetime.combine(appointment.date, appointment.time)
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
        
    session, created = ConsultationSession.objects.get_or_create(
        appointment=appointment,
        defaults={'scheduled_start': dt}
    )
    
    return Response(ConsultationSessionSerializer(session).data, status=status.HTTP_201_CREATED)

@extend_schema(
    request=JoinConsultationRequestSerializer,
    responses={200: ConsultationSessionSerializer},
    tags=['Telemedicine']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_consultation(request, pk):
    """Join a consultation session."""
    try:
        session = ConsultationSession.objects.get(pk=pk)
    except ConsultationSession.DoesNotExist:
        return Response({"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND)
        
    serializer = JoinConsultationRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    role = serializer.validated_data['role']
    
    # Update state
    if session.status == 'SCHEDULED':
        session.status = 'WAITING'
        session.save()
        
    participant, created = ConsultationParticipant.objects.get_or_create(
        session=session,
        user=request.user,
        defaults={'role': role}
    )
    
    participant.joined_at = timezone.now()
    participant.is_active = True
    participant.save()
    
    return Response(ConsultationSessionSerializer(session).data)

@extend_schema(
    request=None,
    responses={200: ConsultationSessionSerializer},
    tags=['Telemedicine']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def end_consultation(request, pk):
    """End a consultation session."""
    try:
        session = ConsultationSession.objects.get(pk=pk)
    except ConsultationSession.DoesNotExist:
        return Response({"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND)
        
    # Only doctor or active participant can end it
    if not ConsultationParticipant.objects.filter(session=session, user=request.user).exists():
        return Response({"error": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)
        
    session.status = 'COMPLETED'
    session.actual_end = timezone.now()
    session.save()
    
    # Set all participants as inactive
    ConsultationParticipant.objects.filter(session=session).update(
        is_active=False, 
        left_at=timezone.now()
    )
    
    return Response(ConsultationSessionSerializer(session).data)

@extend_schema(
    responses={200: ConsultationEventSerializer(many=True)},
    tags=['Telemedicine']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_chat_history(request, pk):
    """Fetch chat history for a session."""
    events = ConsultationEvent.objects.filter(
        session_id=pk, 
        event_type='CHAT'
    ).order_by('timestamp')
    return Response(ConsultationEventSerializer(events, many=True).data)
