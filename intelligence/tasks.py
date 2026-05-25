from celery import shared_task
from .services.anonymizer import PHIAnonymizer
from .services.extractor import DocumentExtractor, MedicalNLP
from ehr.models import DocumentAttachment
from .models import AIAnalysisResult
import logging
import os

logger = logging.getLogger(__name__)

@shared_task
def process_ehr_document(attachment_id):
    logger.info(f"Starting true AI processing for DocumentAttachment ID: {attachment_id}")
    
    try:
        doc = DocumentAttachment.objects.get(id=attachment_id)
        
        # 1. OCR Pipeline: Extract real text from file
        file_path = doc.file.path
        raw_text, extraction_method = DocumentExtractor.extract_text(file_path)
        
        logger.info(f"[{attachment_id}] Extraction Method: {extraction_method}")
        logger.info(f"[{attachment_id}] Extracted Character Count: {len(raw_text)}")
        
        # 2. PHI Anonymization
        clean_text = PHIAnonymizer.anonymize_text(raw_text)
        
        # 3. Medical NLP Summarization (Dynamic)
        analysis = MedicalNLP.analyze(clean_text)
        
        logger.info(f"[{attachment_id}] Detected Conditions: {analysis['conditions']}")
        logger.info(f"[{attachment_id}] Detected Medications: {analysis['medications']}")
        logger.info(f"[{attachment_id}] Confidence Score: {analysis['confidence']}")
        
        if analysis['is_error']:
            logger.error(f"[{attachment_id}] AI Analysis Failed: {analysis['summary']}")
            
        # Add extraction_method to the summary dictionary so we can render it in UI
        ai_summary = {
            "summary": analysis['summary'], 
            "is_error": analysis['is_error'],
            "extraction_method": extraction_method
        }
        
        # 4. Save Results
        AIAnalysisResult.objects.update_or_create(
            document=doc,
            defaults={
                'raw_extracted_text': clean_text,
                'ai_summary': ai_summary,
                'identified_conditions': analysis['conditions'],
                'extracted_medications': analysis['medications'],
                'confidence_score': analysis['confidence']
            }
        )
        
        # 5. Push Real-time WebSocket Notification
        from notifications.services import NotificationService
        patient = doc.ehr_record.patient
        NotificationService.send_notification(
            user=patient,
            n_type='AI_ANALYSIS_READY',
            title='AI Analysis Ready',
            message=f"The AI analysis for your document '{doc.ehr_record.title}' is now ready.",
            priority='high',
            link=f"/ehr/dashboard/"
        )
        
        # Also notify doctor if linked
        for link in doc.ehr_record.appointment_links.all():
            NotificationService.send_notification(
                user=link.appointment.doctor.user,
                n_type='AI_ANALYSIS_READY',
                title='Patient EHR Analysis Ready',
                message=f"AI analysis for {patient.get_full_name()}'s document is complete.",
                priority='normal',
                link=f"/dashboard/doctor/"
            )
        
        logger.info(f"Successfully processed DocumentAttachment ID: {attachment_id}")
        
    except Exception as e:
        logger.error(f"Failed to process DocumentAttachment ID {attachment_id}: {str(e)}")
