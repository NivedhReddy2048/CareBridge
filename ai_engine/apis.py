from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from drf_spectacular.utils import extend_schema
from ai_engine.services.triage_service import TriageService
from ai_engine.services.summary_service import SummaryService
from ai_engine.services.recommendation_service import RecommendationService
from ai_engine.models import AIConversation, AIMessage
from ehr.models import EHRRecord
from ai_engine.throttles import AIHeavyThrottle, AIChatThrottle

class TriageAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AIHeavyThrottle]
    from ai_engine.serializers import TriageRequestSerializer
    serializer_class = TriageRequestSerializer

    @extend_schema(request=TriageRequestSerializer)
    def post(self, request):
        symptoms = request.data.get('symptoms')
        if not symptoms:
            return Response({"error": "Symptoms required"}, status=status.HTTP_400_BAD_REQUEST)
        if len(symptoms) > 1000:
            return Response({"error": "Symptoms text too long. Max 1000 characters allowed."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            result = TriageService.analyze_symptoms(request.user, symptoms)
            return Response(result)
        except Exception as e:
            return Response({"error": "An unexpected error occurred during triage."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SummarizeReportAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AIHeavyThrottle]
    from ai_engine.serializers import SummarizeReportRequestSerializer
    serializer_class = SummarizeReportRequestSerializer

    @extend_schema(request=SummarizeReportRequestSerializer)
    def post(self, request):
        record_id = request.data.get('ehr_record_id')
        raw_text = request.data.get('raw_text', '')
        
        if len(raw_text) > 15000:
            return Response({"error": "OCR text too large for processing. Max 15000 characters allowed."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            record = EHRRecord.objects.get(id=record_id, patient=request.user)
        except EHRRecord.DoesNotExist:
            return Response({"error": "Record not found"}, status=status.HTTP_404_NOT_FOUND)
            
        try:
            result = SummaryService.summarize_ehr(record, raw_text, request.user)
            return Response(result)
        except Exception:
            return Response({"error": "An unexpected error occurred during summarization."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RecommendDoctorsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AIHeavyThrottle]
    from ai_engine.serializers import RecommendDoctorsRequestSerializer
    serializer_class = RecommendDoctorsRequestSerializer

    @extend_schema(request=RecommendDoctorsRequestSerializer)
    def post(self, request):
        triage_result = request.data.get('triage_result', {})
        try:
            result = RecommendationService.recommend_doctors(request.user, triage_result)
            return Response(result)
        except Exception:
            return Response({"error": "An unexpected error occurred during recommendation."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ChatbotAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AIChatThrottle]
    from ai_engine.serializers import ChatbotRequestSerializer
    serializer_class = ChatbotRequestSerializer

    @extend_schema(request=ChatbotRequestSerializer)
    def post(self, request):
        user_message = request.data.get('message', '')
        if len(user_message) > 500:
            return Response({"error": "Message too long. Max 500 characters allowed."}, status=status.HTTP_400_BAD_REQUEST)
            
        conversation_id = request.data.get('conversation_id')
        
        if conversation_id:
            try:
                conv = AIConversation.objects.get(id=conversation_id, patient=request.user)
            except AIConversation.DoesNotExist:
                return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            conv = AIConversation.objects.create(patient=request.user)
            
        # Save user msg
        AIMessage.objects.create(conversation=conv, role='user', message=user_message)
        
        # Simple fallback response for chatbot structure
        # (A real implementation would pass the history to Gemini)
        ai_reply = "I am the CareBridge AI Assistant. I have recorded your symptoms. Please use the triage feature or book an appointment for further diagnosis."
        
        from ai_engine.clients.gemini_client import gemini_client
        try:
            history = list(conv.messages.order_by('timestamp').values('role', 'message'))
            prompt = f"You are a helpful healthcare assistant. History: {history}. User says: {user_message}. Output strictly JSON: {{'reply': 'your response'}}"
            res = gemini_client.generate_json(prompt, user=request.user, endpoint="chatbot")
            ai_reply = res.get('reply', ai_reply)
        except Exception:
            pass
            
        AIMessage.objects.create(conversation=conv, role='model', message=ai_reply)
        
        return Response({
            "conversation_id": conv.id,
            "reply": ai_reply
        })
