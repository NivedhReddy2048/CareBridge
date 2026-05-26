import re

class FallbackEngine:
    @staticmethod
    def triage_fallback(symptoms_text):
        """Regex-based fallback for triage if Gemini fails."""
        text = symptoms_text.lower()
        
        critical_keywords = [
            'heart attack', 'stroke', 'suicide', 'breathing', 'choking', 
            'unconscious', 'severe bleeding', 'seizure', 'chest pain', 'difficulty breathing'
        ]
        high_keywords = ['fracture', 'broken bone', 'severe pain', 'fainted']
        
        urgency = "LOW"
        department = "General Physician"
        emergency_risk = False
        
        for word in critical_keywords:
            if re.search(r'\b' + re.escape(word) + r'\b', text):
                urgency = "CRITICAL"
                department = "Emergency"
                emergency_risk = True
                break
                
        if urgency == "LOW":
            for word in high_keywords:
                if re.search(r'\b' + re.escape(word) + r'\b', text):
                    urgency = "HIGH"
                    department = "Orthopedic" if "bone" in word or "fracture" in word else "General Physician"
                    break
                    
        disclaimer = "\n\nDisclaimer: AI recommendations are informational only and do not replace professional medical consultation."
        recommendation = "Based on keywords matching. Please consult a doctor for a proper diagnosis." + disclaimer
        if emergency_risk:
            recommendation += "\n\nCRITICAL: Please seek immediate medical attention or call emergency services."

        return {
            "urgency": urgency,
            "department": department,
            "emergency_risk": emergency_risk,
            "recommendation": recommendation,
            "confidence": 0.5
        }

    @staticmethod
    def summary_fallback(text):
        return {
            "summary": "AI summarization is currently unavailable. Please read the full text.",
            "conditions": [],
            "medications": [],
            "confidence": 0.0
        }
