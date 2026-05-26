import json
import logging
from celery import shared_task
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import AIProcessingJob, AIProcessingResult, ConsultationTranscriptChunk, AIInferenceEvent
from telemedicine.models import ConsultationSession
from clinical_intelligence.services.ai_analyzer import ClinicalIntelligenceService

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_consultation_intelligence(self, session_id):
    """
    Background task to process recent transcript chunks for a session
    and generate clinical intelligence (symptoms, risks, summary).
    """
    job = None
    try:
        session = ConsultationSession.objects.get(id=session_id)
        
        # Create or update job state
        job = AIProcessingJob.objects.create(
            session=session,
            job_type='TRANSCRIPT_SUMMARY',
            status='PROCESSING'
        )
        
        AIInferenceEvent.objects.create(job=job, event_type='START', message=f'Starting inference for session {session_id}')
        
        # We assume ClinicalIntelligenceService now handles the chunks (we pass patient)
        # We need to adapt it slightly to use the patient from session.appointment
        patient = session.appointment.patient
        
        result = ClinicalIntelligenceService.analyze_consultation_events(session_id, patient)
        
        if result:
            AIProcessingResult.objects.create(
                job=job,
                result_payload=result,
                tokens_used=500, # Mocked token usage
                latency_ms=1200 # Mocked latency
            )
            job.status = 'COMPLETED'
            job.save()
            AIInferenceEvent.objects.create(job=job, event_type='SUCCESS', message='Inference completed successfully.')
            
            # Broadcast the AI summary updated event over WebSockets
            channel_layer = get_channel_layer()
            room_group_name = f"telemedicine_{session_id}"
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'broadcast_message',
                    'event_type': 'AI_UPDATE',
                    'payload': result,
                    'sender_id': None
                }
            )
            
            # Broadcast to enterprise observers
            async_to_sync(channel_layer.group_send)(
                "enterprise_telemedicine",
                {
                    'type': 'broadcast_message',
                    'event_type': 'AI_JOB_COMPLETED',
                    'payload': {'session_id': str(session_id), 'job_id': str(job.id)}
                }
            )
        else:
            raise Exception("AI Intelligence generated empty result (fallback triggered)")
            
    except Exception as e:
        logger.error(f"AI Task failed: {e}")
        if job:
            job.status = 'RETRYING' if self.request.retries < self.max_retries else 'FAILED'
            job.retry_count = self.request.retries
            job.save()
            AIInferenceEvent.objects.create(job=job, event_type='ERROR', message=str(e), is_error=True)
            
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
