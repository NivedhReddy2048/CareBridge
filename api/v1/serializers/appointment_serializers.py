from rest_framework import serializers
from appointments.models import Appointment, Doctor
from api.v1.serializers.auth_serializers import UserSerializer

class DoctorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Doctor
        fields = ['id', 'user', 'specialization', 'qualification', 'experience_years', 'consultation_fee', 'is_available']

class AppointmentSerializer(serializers.ModelSerializer):
    doctor_details = DoctorSerializer(source='doctor', read_only=True)
    patient_details = UserSerializer(source='patient', read_only=True)
    
    class Meta:
        model = Appointment
        fields = ['id', 'patient', 'patient_details', 'doctor', 'doctor_details', 'date', 'time', 'reason', 'status', 'meeting_link', 'created_at']
        read_only_fields = ['patient', 'status', 'meeting_link', 'created_at']

class AppointmentBookingSerializer(serializers.Serializer):
    doctor_id = serializers.IntegerField()
    date = serializers.DateField()
    time = serializers.TimeField()
    reason = serializers.CharField(max_length=500)
    ehr_file = serializers.FileField(required=False)
