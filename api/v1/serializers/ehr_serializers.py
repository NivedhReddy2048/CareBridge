from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from ehr.models import EHRRecord, DocumentAttachment
from intelligence.models import AIAnalysisResult

class AIAnalysisResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIAnalysisResult
        fields = ['id', 'ai_summary', 'identified_conditions', 'extracted_medications', 'confidence_score', 'raw_extracted_text', 'processed_at']

class DocumentAttachmentSerializer(serializers.ModelSerializer):
    ai_analysis = AIAnalysisResultSerializer(read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = DocumentAttachment
        fields = ['id', 'file_url', 'uploaded_at', 'ai_analysis']

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None

class EHRRecordSerializer(serializers.ModelSerializer):
    attachments = DocumentAttachmentSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    record_type_display = serializers.CharField(source='get_record_type_display', read_only=True)

    class Meta:
        model = EHRRecord
        fields = ['id', 'patient', 'patient_name', 'title', 'record_type', 'record_type_display', 'date_of_record', 'notes', 'created_at', 'attachments']
        read_only_fields = ['patient']

class EHRUploadSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    record_type = serializers.ChoiceField(choices=EHRRecord.RECORD_TYPES)
    date_of_record = serializers.DateField()
    notes = serializers.CharField(required=False, allow_blank=True)
    file = serializers.FileField()
