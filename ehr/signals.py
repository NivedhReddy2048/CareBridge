from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import DocumentAttachment
from intelligence.tasks import process_ehr_document

@receiver(post_save, sender=DocumentAttachment)
def trigger_ai_processing(sender, instance, created, **kwargs):
    """
    Triggers asynchronous AI processing (OCR + LLM Summarization) 
    whenever a new medical document is uploaded.
    """
    if created:
        # Push to Celery queue asynchronously
        process_ehr_document.delay(instance.id)
