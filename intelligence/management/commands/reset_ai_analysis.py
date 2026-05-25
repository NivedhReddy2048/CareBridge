from django.core.management.base import BaseCommand
from intelligence.models import AIAnalysisResult
from ehr.models import DocumentAttachment
from intelligence.tasks import process_ehr_document

class Command(BaseCommand):
    help = 'Clears all stale AI Analysis results and optionally reprocesses them through the OCR pipeline.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reprocess',
            action='store_true',
            help='Reprocess all existing EHR documents after deleting old results.',
        )

    def handle(self, *args, **options):
        # 1. Delete all existing records to clear cache
        count, _ = AIAnalysisResult.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} stale AIAnalysisResult records.'))

        # 2. Optionally reprocess
        if options['reprocess']:
            self.stdout.write(self.style.WARNING('Reprocessing all existing DocumentAttachments via new OCR pipeline...'))
            attachments = DocumentAttachment.objects.all()
            for doc in attachments:
                self.stdout.write(f'Queueing OCR for DocumentAttachment ID: {doc.id}...')
                process_ehr_document.delay(doc.id)
            self.stdout.write(self.style.SUCCESS(f'Successfully queued {attachments.count()} documents for reprocessing.'))
