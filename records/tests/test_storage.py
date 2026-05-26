import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from records.services.file_security_service import FileSecurityService
from django.core.exceptions import ValidationError

def test_file_security_valid_pdf():
    # create a dummy PDF file (has %PDF header)
    content = b"%PDF-1.4\n%...\n"
    file = SimpleUploadedFile("test.pdf", content, content_type="application/pdf")
    
    # Should not raise exception
    FileSecurityService.validate_upload(file)

def test_file_security_invalid_extension():
    content = b"MZ\x90\x00\x03\x00\x00\x00" # Exe header
    file = SimpleUploadedFile("virus.exe", content, content_type="application/x-msdownload")
    
    with pytest.raises(ValidationError) as exc:
        FileSecurityService.validate_upload(file)
    assert 'prohibited' in str(exc.value)

def test_file_security_spoofed_mime():
    # Claim it's a PDF but it's an executable
    content = b"MZ\x90\x00\x03\x00\x00\x00" 
    file = SimpleUploadedFile("fake.pdf", content, content_type="application/pdf")
    
    with pytest.raises(ValidationError) as exc:
        FileSecurityService.validate_upload(file)
    # The magic checker will reject it
    assert 'Type mismatch' in str(exc.value) or 'not match' in str(exc.value) or 'not allowed' in str(exc.value)
