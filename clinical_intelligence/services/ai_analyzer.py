import json
import logging
from ai_engine.clients.gemini_client import gemini_client
from telemedicine.models import ConsultationEvent
from clinical_intelligence.models import ClinicalInsightEvent

logger = logging.getLogger(__name__)

class ClinicalIntelligenceService:
    @staticmethod
    def analyze_consultation_events(session_id, patient):
        """Analyze chat/transcription history of a consultation and extract intelligence."""
        try:
            events = ConsultationEvent.objects.filter(session_id=session_id, event_type__in=['CHAT', 'SIGNAL']).order_by('timestamp')
            
            # Build conversation transcript
            transcript = ""
            for event in events:
                sender = event.sender.username if event.sender else "System"
                text = event.payload.get('text', '')
                if text:
                    transcript += f"{sender}: {text}\n"
                    
            if not transcript:
                return None
                
            prompt = f"""
            Analyze the following live medical consultation transcript.
            Identify any symptoms, potential risks, and generate a brief summary.
            Output STRICT JSON ONLY:
            {{
                "symptoms_extracted": ["symptom1", "symptom2"],
                "risks_identified": ["risk1"],
                "summary": "brief summary",
                "emergency_escalation": true/false
            }}
            
            Transcript:
            {transcript}
            """
            
            raw_res = gemini_client.generate_json(prompt, user=patient, endpoint="clinical_intelligence")
            
            # Save Insights
            if raw_res.get('emergency_escalation'):
                ClinicalInsightEvent.objects.create(
                    patient=patient,
                    insight_type="EMERGENCY_RISK",
                    description="AI detected emergency risk from live consultation.",
                    confidence=0.9,
                    related_consultation_id=session_id
                )
                
            if raw_res.get('risks_identified'):
                ClinicalInsightEvent.objects.create(
                    patient=patient,
                    insight_type="POTENTIAL_RISKS",
                    description=", ".join(raw_res['risks_identified']),
                    confidence=0.8,
                    related_consultation_id=session_id
                )
                
            return raw_res
            
        except Exception as e:
            logger.error(f"ClinicalIntelligenceService failed: {e}")
            return None
