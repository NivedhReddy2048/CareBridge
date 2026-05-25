import ssl
from django.core.mail.backends.smtp import EmailBackend

class CustomEmailBackend(EmailBackend):
    """
    A custom email backend that ignores SSL certificate errors.
    Useful for development when Antivirus software intercepts connections.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Create an SSL context that ignores certificate verification
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE