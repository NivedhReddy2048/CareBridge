import magic
import os
import uuid
from django.core.exceptions import ValidationError
from django.utils import timezone

class FileSecurityService:
    ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png'}
    ALLOWED_MIME_TYPES = {'application/pdf', 'image/jpeg', 'image/png'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    BLOCKED_EXTENSIONS = {'.exe', '.bat', '.sh', '.js', '.vbs', '.scr'}

    @classmethod
    def validate_upload(cls, file_obj):
        """Validates file extension, size, and true MIME type."""
        # 1. Size Validation
        if file_obj.size > cls.MAX_FILE_SIZE:
            raise ValidationError(f"File size exceeds maximum limit of {cls.MAX_FILE_SIZE / (1024*1024)} MB.")
            
        # 2. Extension Validation
        ext = os.path.splitext(file_obj.name)[1].lower()
        if ext in cls.BLOCKED_EXTENSIONS:
            raise ValidationError("Executable files are strictly prohibited.")
        if ext not in cls.ALLOWED_EXTENSIONS:
            raise ValidationError(f"Unsupported file type: {ext}. Allowed types are: {', '.join(cls.ALLOWED_EXTENSIONS)}")
            
        # Check for double extensions (e.g., report.pdf.exe)
        base_name = os.path.basename(file_obj.name)
        if base_name.count('.') > 1:
            raise ValidationError("Suspicious filename detected. Multiple extensions are not allowed.")

        # 3. True MIME Type Validation (Magic Numbers)
        # Read a chunk to guess mime
        chunk = file_obj.read(2048)
        file_obj.seek(0) # Reset pointer
        mime_type = magic.from_buffer(chunk, mime=True)
        
        if mime_type not in cls.ALLOWED_MIME_TYPES:
            raise ValidationError(f"File content does not match allowed types. Detected: {mime_type}")
            
        # 4. Sanitize Filename (return secure name)
        secure_name = f"{uuid.uuid4().hex}{ext}"
        
        return {
            'is_valid': True,
            'secure_filename': secure_name,
            'mime_type': mime_type,
            'original_name': file_obj.name
        }

    @classmethod
    def scan_file(cls, ehr_record, file_obj):
        """
        Async-ready architecture for malware scanning.
        Currently logs the file as pending and simulates a clean scan.
        """
        from records.models import MalwareScanLog
        
        scan_log = MalwareScanLog.objects.create(
            ehr_record=ehr_record,
            filename=file_obj.name,
            status='PENDING',
            scan_provider='CLAMAV_STUB'
        )
        
        try:
            # TODO: Integrate ClamAV or AWS Lambda scanner here.
            # Simulate scan passing:
            is_clean = True 
            
            if is_clean:
                scan_log.status = 'CLEAN'
            else:
                scan_log.status = 'INFECTED'
            scan_log.save()
            return is_clean
            
        except Exception as e:
            scan_log.status = 'FAILED'
            scan_log.save()
            # Depending on policy, we might quarantine if failed
            return False
