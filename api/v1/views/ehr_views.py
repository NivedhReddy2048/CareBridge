from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404

from ehr.models import EHRRecord, DocumentAttachment, AuditLog
from intelligence.models import AIAnalysisResult
from api.v1.serializers.ehr_serializers import EHRRecordSerializer, EHRUploadSerializer, AIAnalysisResultSerializer
from api.v1.permissions import IsPatient, IsDoctor

class EHRViewSet(viewsets.ModelViewSet):
    serializer_class = EHRRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return EHRRecord.objects.none()
            
        if getattr(user, 'role', None) == 'patient':
            return EHRRecord.objects.filter(patient=user)
        elif getattr(user, 'role', None) == 'doctor':
            # Doctors can only see records linked to their appointments
            return EHRRecord.objects.filter(appointment_links__appointment__doctor__user=user).distinct()
        elif getattr(user, 'role', None) == 'admin' or user.is_staff:
            return EHRRecord.objects.all()
        return EHRRecord.objects.none()

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser], permission_classes=[IsPatient])
    def upload(self, request):
        serializer = EHRUploadSerializer(data=request.data)
        if serializer.is_valid():
            uploaded_file = serializer.validated_data['file']
            
            # Phase 8: Secure Validation
            try:
                from records.services.file_security_service import FileSecurityService
                validation_result = FileSecurityService.validate_upload(uploaded_file)
                # Overwrite filename safely
                uploaded_file.name = validation_result['secure_filename']
            except Exception as e:
                # Catch ValidationError or others and return safe 400
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
                
            # Create Record
            record = EHRRecord.objects.create(
                patient=request.user,
                title=serializer.validated_data['title'],
                record_type=serializer.validated_data['record_type'],
                date_of_record=serializer.validated_data['date_of_record'],
                notes=serializer.validated_data.get('notes', '')
            )
            # Create Attachment
            attachment = DocumentAttachment.objects.create(
                ehr_record=record,
                file=uploaded_file,
                file_type=validation_result.get('mime_type')
            )
            
            # Phase 8: Trigger Malware Scan Asynchronously
            # Currently synchronous for MVP but async-ready
            FileSecurityService.scan_file(record, uploaded_file)
            
            # Audit log
            # Since we imported AuditLog from ehr.models, wait... it was originally created as AuditLog in ehr.models but missing some fields.
            # No, looking at ehr.models.py AuditLog, it expects `user`, `ehr_record`, `action`
            from ehr.models import AuditLog as EHRAuditLog
            EHRAuditLog.objects.create(
                ehr_record=record,
                user=request.user,
                action='UPLOAD',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            return Response(EHRRecordSerializer(record, context={'request': request}).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        record = self.get_object()
        if request.user.role != 'patient' or record.patient != request.user:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
        record.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def ai_summary(self, request, pk=None):
        record = self.get_object()
        attachment = record.attachments.first()
        if not attachment:
            return Response({"error": "No attachment found for this record."}, status=status.HTTP_404_NOT_FOUND)
            
        ai_result = AIAnalysisResult.objects.filter(document=attachment).first()
        if not ai_result:
            return Response({"status": "processing", "message": "AI analysis is currently running."}, status=status.HTTP_202_ACCEPTED)
            
        return Response(AIAnalysisResultSerializer(ai_result).data)
