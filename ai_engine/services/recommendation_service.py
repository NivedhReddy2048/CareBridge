import logging
from ai_engine.clients.gemini_client import gemini_client
from appointments.models import Doctor
from ai_engine.constants import DEPARTMENT_SPECIALIZATION_MAP
from django.db.models import Q

logger = logging.getLogger(__name__)

class RecommendationService:
    @staticmethod
    def recommend_doctors(patient, triage_result):
        department = triage_result.get('department', 'General Physician')
        logger.info(f"AI Department: {department}")
        
        # Get mapping aliases or fallback to exact department string
        aliases = DEPARTMENT_SPECIALIZATION_MAP.get(department, [department])
        
        doctors_qs = Doctor.objects.select_related('user').filter(is_verified=True, is_available=True)
        
        # Safely query using Q objects for icontains on all aliases
        q_objects = Q()
        for alias in aliases:
            q_objects |= Q(specialization__icontains=alias)
            
        department_docs = doctors_qs.filter(q_objects).order_by('-experience_years')[:3]
        
        # We explicitly do NOT want to fallback to random doctors if specialization doesn't match
        # However, for an emergency, we might want any available doctor. For now, strict matching.
        logger.info(f"Matched Doctors: {department_docs.count()}")
            
        recommended_doctors = []
        for d in department_docs:
            recommended_doctors.append({
                "id": d.id,
                "name": f"Dr. {d.user.first_name} {d.user.last_name}".strip() or f"Dr. {d.user.username}",
                "specialization": d.specialization,
                "experience": d.experience_years,
                "rating": 4.8
            })
            
        triage_result['recommended_doctors'] = recommended_doctors
        return triage_result
