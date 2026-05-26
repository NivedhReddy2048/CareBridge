from rest_framework import serializers

class TriageRequestSerializer(serializers.Serializer):
    symptoms = serializers.CharField(max_length=1000)

class SummarizeReportRequestSerializer(serializers.Serializer):
    ehr_record_id = serializers.IntegerField()
    raw_text = serializers.CharField(max_length=15000, required=False, allow_blank=True)

class RecommendDoctorsRequestSerializer(serializers.Serializer):
    triage_result = serializers.DictField()

class ChatbotRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=500)
    conversation_id = serializers.IntegerField(required=False, allow_null=True)
