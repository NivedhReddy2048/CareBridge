import razorpay
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class RazorpayClient:
    def __init__(self):
        self.key_id = getattr(settings, 'RAZORPAY_KEY_ID', None)
        self.key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', None)
        
        if not self.key_id or not self.key_secret:
            logger.warning("Razorpay credentials not found in settings. Payment features will fail.")
            self.client = None
        else:
            self.client = razorpay.Client(auth=(self.key_id, self.key_secret))

    def create_order(self, amount_in_inr, receipt_id, notes=None):
        if not self.client:
            raise ValueError("Razorpay client not configured.")
        
        # Razorpay expects amount in paisa
        amount_in_paisa = int(amount_in_inr * 100)
        
        data = {
            "amount": amount_in_paisa,
            "currency": "INR",
            "receipt": str(receipt_id),
            "notes": notes or {}
        }
        
        try:
            return self.client.order.create(data=data)
        except Exception as e:
            logger.error(f"Failed to create Razorpay order: {str(e)}")
            raise

    def verify_signature(self, razorpay_order_id, razorpay_payment_id, razorpay_signature):
        if not self.client:
            raise ValueError("Razorpay client not configured.")
        
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        try:
            self.client.utility.verify_payment_signature(params_dict)
            return True
        except razorpay.errors.SignatureVerificationError:
            logger.error("Razorpay signature verification failed.")
            return False
        except Exception as e:
            logger.error(f"Error verifying Razorpay signature: {str(e)}")
            return False
