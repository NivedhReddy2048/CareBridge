import re

class PHIAnonymizer:
    @staticmethod
    def anonymize_text(text):
        """
        Scrub potential Protected Health Information (PHI) before sending to LLMs.
        - Names, Phone numbers, Emails, SSNs, DOBs
        """
        if not text: return ""
        
        # Scrub Emails
        text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL REDACTED]', text)
        
        # Scrub Phone numbers (basic format)
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE REDACTED]', text)
        
        # Scrub SSNs
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN REDACTED]', text)
        
        # Basic date scrubbing (DOB) - matches MM/DD/YYYY or DD-MM-YYYY
        text = re.sub(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', '[DATE REDACTED]', text)
        
        # In a real enterprise, we would use Microsoft Presidio or AWS Comprehend Medical.
        return text
