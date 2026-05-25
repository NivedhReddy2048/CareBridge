import logging
from analytics.models import AITriageEstimate

logger = logging.getLogger(__name__)

class TriageEngine:
    """
    Simulated AI Triage Engine to prioritize patient appointments.
    In a real enterprise, this would call an LLM (e.g. OpenAI/Google Vertex).
    """
    
    @staticmethod
    def estimate_triage(symptoms: str, patient, appointment=None) -> AITriageEstimate:
        symptoms_lower = symptoms.lower()
        
        urgency = 'LOW'
        department = 'General Medicine'
        confidence = 0.85
        reasoning = "Routine symptoms detected."

        if any(word in symptoms_lower for word in ['chest pain', 'heart', 'stroke', 'breathing', 'severe bleeding']):
            urgency = 'CRITICAL'
            department = 'Emergency Cardiology / Trauma'
            confidence = 0.95
            reasoning = "Critical keywords detected indicating possible life-threatening condition."
        elif any(word in symptoms_lower for word in ['fracture', 'broken bone', 'severe pain', 'accident']):
            urgency = 'HIGH'
            department = 'Orthopedics / Trauma'
            confidence = 0.90
            reasoning = "High severity physical trauma indicators found."
        elif any(word in symptoms_lower for word in ['fever', 'cough', 'flu', 'infection']):
            urgency = 'MEDIUM'
            department = 'General Medicine'
            confidence = 0.88
            reasoning = "Moderate infection symptoms."

        estimate = AITriageEstimate.objects.create(
            patient=patient,
            appointment=appointment,
            symptoms=symptoms,
            urgency_level=urgency,
            recommended_department=department,
            confidence_score=confidence,
            reasoning=reasoning
        )
        logger.info(f"Generated Triage Estimate for {patient.username}: {urgency} -> {department}")
        return estimate
