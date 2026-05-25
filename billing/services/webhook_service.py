import hmac
import hashlib
import json
from django.conf import settings
from billing.models import Transaction
from billing.constants import PaymentStatus
import logging

logger = logging.getLogger(__name__)

class WebhookService:
    def __init__(self):
        self.webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', '')

    def verify_webhook_signature(self, payload, signature):
        if not self.webhook_secret:
            logger.warning("Webhook secret not set. Skipping signature validation.")
            return True
        
        expected_signature = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)

    def process_webhook(self, event_data):
        event = event_data.get('event')
        
        if event == 'payment.captured':
            self._handle_payment_captured(event_data)
        elif event == 'payment.failed':
            self._handle_payment_failed(event_data)
            
    def _handle_payment_captured(self, event_data):
        payment_entity = event_data['payload']['payment']['entity']
        order_id = payment_entity.get('order_id')
        
        if not order_id:
            return
            
        try:
            txn = Transaction.objects.get(razorpay_order_id=order_id)
            if txn.payment_status != PaymentStatus.SUCCESS:
                # Fallback if frontend failed to confirm
                from .payment_service import PaymentService
                service = PaymentService()
                # Assuming signature verified in webhook, we simulate success
                txn.payment_status = PaymentStatus.SUCCESS
                txn.razorpay_payment_id = payment_entity.get('id')
                txn.save()
                
                # generate invoice if missing
                if not hasattr(txn, 'invoice'):
                    service._generate_invoice(txn)
                    
        except Transaction.DoesNotExist:
            logger.error("Webhook received for unknown order: %s", order_id)

    def _handle_payment_failed(self, event_data):
        payment_entity = event_data['payload']['payment']['entity']
        order_id = payment_entity.get('order_id')
        error_description = payment_entity.get('error_description', 'Payment failed')
        
        if not order_id:
            return
            
        try:
            txn = Transaction.objects.get(razorpay_order_id=order_id)
            if txn.payment_status == PaymentStatus.PENDING:
                txn.payment_status = PaymentStatus.FAILED
                txn.failure_reason = error_description
                txn.save()
        except Transaction.DoesNotExist:
            pass
