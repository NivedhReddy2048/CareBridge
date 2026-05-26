from rest_framework import serializers
from .models import ConsultationSession, ConsultationParticipant, ConsultationEvent

class ConsultationParticipantSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = ConsultationParticipant
        fields = ['id', 'username', 'full_name', 'role', 'joined_at', 'left_at', 'is_active']

class ConsultationSessionSerializer(serializers.ModelSerializer):
    participants = ConsultationParticipantSerializer(many=True, read_only=True)
    
    class Meta:
        model = ConsultationSession
        fields = ['id', 'appointment', 'status', 'scheduled_start', 'actual_start', 'actual_end', 'participants', 'created_at']

class ConsultationEventSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.username', read_only=True, default="System")
    
    class Meta:
        model = ConsultationEvent
        fields = ['id', 'sender_name', 'event_type', 'payload', 'timestamp']

class CreateConsultationRequestSerializer(serializers.Serializer):
    appointment_id = serializers.IntegerField()

class JoinConsultationRequestSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=['DOCTOR', 'PATIENT', 'OBSERVER'])
