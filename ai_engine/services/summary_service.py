from ai_engine.clients.gemini_client import gemini_client
from ai_engine.services.fallback_service import FallbackEngine
from ai_engine.models import AISummaryCache
from django.utils import timezone
import datetime

class SummaryService:
    @staticmethod
    def summarize_ehr(ehr_record, raw_text, user):
        # Check cache first
        cached = AISummaryCache.objects.filter(ehr_record=ehr_record, expires_at__gt=timezone.now()).first()
        if cached:
            import json
            try:
                return json.loads(cached.summary)
            except:
                pass
                
        prompt = f"""
        You are an expert medical AI. Summarize the following raw Electronic Health Record text.
        Output STRICT JSON only.
        
        Raw text: {raw_text}
        
        Output format:
        {{
            "summary": "Clear, concise summary of the patient's condition",
            "conditions": ["Condition 1", "Condition 2"],
            "medications": ["Med 1", "Med 2"],
            "confidence": 0.0 to 1.0
        }}
        """
        
        try:
            result = gemini_client.generate_json(prompt, user=user, endpoint="summary")
            import json
            # Cache it
            AISummaryCache.objects.update_or_create(
                ehr_record=ehr_record,
                defaults={
                    'summary': json.dumps(result),
                    'confidence': result.get('confidence', 0.0),
                    'expires_at': timezone.now() + datetime.timedelta(days=7)
                }
            )
            return result
        except Exception:
            return FallbackEngine.summary_fallback(raw_text)
