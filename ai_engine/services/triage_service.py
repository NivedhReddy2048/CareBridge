import json
from ai_engine.clients.gemini_client import gemini_client
from ai_engine.services.fallback_service import FallbackEngine
from ai_engine.services.emergency_service import EmergencyService
from ai_engine.utils.response_parser import ResponseParser
from ai_engine.validators import MedicalValidator
from ai_engine.models import AIAuditLog

class TriageService:
    @staticmethod
    def analyze_symptoms(patient, symptoms_text):
        prompt = f"""
        You are an expert AI triage system for a hospital. 
        Analyze the following patient symptoms and output STRICT JSON only.
        
        Symptoms: {symptoms_text}
        
        Output format:
        {{
            "urgency": "LOW|MEDIUM|HIGH|CRITICAL",
            "department": "Name of medical department (e.g. Cardiology, Emergency, General Physician)",
            "emergency_risk": true/false,
            "recommendation": "Brief recommendation for the patient",
            "confidence": 0.0 to 1.0
        }}
        """
        
        fallback_used = False
        fallback_reason = None
        raw_res = None
        parsed_res = None
        
        try:
            raw_res = gemini_client.generate_json(prompt, user=patient, endpoint="triage")
            parsed_res = ResponseParser.parse_triage_json(json.dumps(raw_res))
            parsed_res = MedicalValidator.validate_triage(parsed_res)
        except Exception as e:
            fallback_used = True
            fallback_reason = str(e)
            parsed_res = FallbackEngine.triage_fallback(symptoms_text)
            
        # Emergency hook
        EmergencyService.handle_emergency(patient, parsed_res)
        
        # Audit logging
        try:
            AIAuditLog.objects.create(
                user=patient,
                raw_prompt=symptoms_text,
                cleaned_prompt=prompt,
                raw_response=json.dumps(raw_res) if raw_res else None,
                parsed_response=parsed_res,
                fallback_reason=fallback_reason,
                emergency_escalation=parsed_res.get('emergency_risk', False)
            )
        except Exception:
            pass
            
        return parsed_res
