import resend
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def send_otp_email(email, otp, subject="CareBridge - Verify Your Account"):
    """
    Sends an OTP email using the Resend HTTPS API.
    Provides structured logging and bypasses SMTP blocks.
    """
    if not settings.RESEND_API_KEY:
        logger.error("RESEND_API_KEY is not configured.")
        raise ValueError("Email service is improperly configured.")

    resend.api_key = settings.RESEND_API_KEY
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: #2c3e50;">CareBridge Security</h2>
        <p>Your verification code is: <strong style="font-size: 24px; color: #e74c3c;">{otp}</strong></p>
        <p>This code will expire shortly. Do not share this code with anyone.</p>
        <hr style="border: 1px solid #ecf0f1; margin-top: 20px;">
        <small style="color: #7f8c8d;">This is an automated message from CareBridge. Please do not reply.</small>
    </div>
    """

    params = {
        "from": settings.DEFAULT_FROM_EMAIL,
        "to": [email],
        "subject": subject,
        "html": html_content,
    }

    try:
        # Resend API call over HTTPS (port 443)
        response = resend.Emails.send(params)
        logger.info(f"Successfully sent OTP to {email} via Resend. ID: {response.get('id')}")
        return True
    except Exception as e:
        exc_type = type(e).__name__
        msg = str(e)
        logger.error(f"RESEND API ERROR | Type: {exc_type} | Message: {msg}")
        print(f"\n================================\nCAREBRIDGE EMAIL ERROR\nProvider: Resend API\nType: {exc_type}\nMessage: {msg}\n=======================\n")
        raise Exception(f"Failed to deliver email: {msg}")
