from django.db import transaction
from django.utils import timezone
from billing.models import Transaction, Invoice
from billing.constants import PaymentStatus
from appointments.models import Appointment
from .razorpay_client import RazorpayClient
import logging
import uuid

logger = logging.getLogger(__name__)

class PaymentService:
    def __init__(self):
        self.rzp_client = RazorpayClient()

    @transaction.atomic
    def create_checkout_session(self, patient, appointment_id):
        appointment = Appointment.objects.get(id=appointment_id, patient=patient)
        
        # Check if already paid
        existing_txn = Transaction.objects.filter(
            appointment=appointment, 
            payment_status=PaymentStatus.SUCCESS
        ).first()
        
        if existing_txn:
            raise ValueError("Appointment is already paid for.")
        
        # Fee logic: default to 500 if doctor has no fee set
        fee = getattr(appointment.doctor, 'consultation_fee', 500.00)
        
        # Create pending transaction
        txn = Transaction.objects.create(
            patient=patient,
            appointment=appointment,
            amount=fee,
            payment_status=PaymentStatus.PENDING
        )
        
        # Create Razorpay order
        order = self.rzp_client.create_order(
            amount_in_inr=fee,
            receipt_id=f"receipt_txn_{txn.id}",
            notes={"appointment_id": appointment.id, "patient_id": patient.id}
        )
        
        txn.razorpay_order_id = order['id']
        txn.save()
        
        return {
            "order_id": order['id'],
            "amount": order['amount'],
            "currency": order['currency'],
            "key_id": self.rzp_client.key_id,
            "transaction_id": txn.id
        }

    @transaction.atomic
    def verify_and_confirm_payment(self, razorpay_order_id, razorpay_payment_id, razorpay_signature):
        logger.info(f"Starting verification for Order ID: {razorpay_order_id}")
        
        # 1. Verify Signature
        try:
            is_valid = self.rzp_client.verify_signature(
                razorpay_order_id, razorpay_payment_id, razorpay_signature
            )
        except Exception as e:
            logger.error(f"Signature verification threw exception for {razorpay_order_id}: {str(e)}")
            raise ValueError("Error validating signature with Razorpay.")
            
        if not is_valid:
            logger.error(f"Payment signature verification failed for order: {razorpay_order_id}")
            raise ValueError("Invalid payment signature.")
        
        # 2. Update Transaction
        try:
            txn = Transaction.objects.select_for_update().get(razorpay_order_id=razorpay_order_id)
            
            if txn.payment_status == PaymentStatus.SUCCESS:
                logger.info(f"Transaction {txn.id} is already marked as SUCCESS. Returning idempotently.")
                return txn # Idempotent return
            
            logger.info(f"Updating Transaction {txn.id} to SUCCESS.")
            txn.payment_status = PaymentStatus.SUCCESS
            txn.razorpay_payment_id = razorpay_payment_id
            txn.razorpay_signature = razorpay_signature
            txn.completed_at = timezone.now()
            txn.save()
            logger.info(f"Transaction {txn.id} updated successfully.")
            
        except Exception as e:
            logger.error(f"Failed to update transaction for order {razorpay_order_id}: {str(e)}")
            raise
        
        # 3. Update Appointment Status
        try:
            appointment = txn.appointment
            logger.info(f"Updating appointment {appointment.id} status. Current status: {appointment.status}")
            if appointment.status == 'pending':
                appointment.status = 'confirmed'
                appointment.save()
                logger.info(f"Appointment {appointment.id} successfully confirmed.")
        except Exception as e:
            logger.error(f"Failed to update appointment status for txn {txn.id}: {str(e)}")
            # Not raising exception here to prevent transaction rollback since payment succeeded
            
        # 4. Generate Invoice Record
        try:
            self._generate_invoice(txn)
        except Exception as e:
            logger.error(f"Failed to generate invoice for txn {txn.id}: {str(e)}")
            # Not raising exception here to prevent transaction rollback since payment succeeded
        
        return txn

    def _generate_invoice(self, txn):
        # Simple invoice creation
        logger.info(f"Generating invoice for Transaction {txn.id}...")
        invoice_number = f"INV-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        invoice = Invoice.objects.create(
            transaction=txn,
            invoice_number=invoice_number,
            subtotal=txn.amount,
            tax_amount=0,
            total_amount=txn.amount
        )
        logger.info(f"Invoice {invoice.invoice_number} generated successfully.")
        return invoice
