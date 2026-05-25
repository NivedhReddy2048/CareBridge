from django.db import models
from django.conf import settings
from appointments.models import Appointment
from .constants import PaymentStatus, PaymentMethod

class Transaction(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='transactions')
    appointment = models.ForeignKey(Appointment, on_delete=models.PROTECT, related_name='billing_transactions')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.RAZORPAY)
    
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    
    gateway_response = models.JSONField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    refunded_at = models.DateTimeField(blank=True, null=True)
    failure_reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"TXN-{self.id} | {self.patient.username} | {self.payment_status}"

class Invoice(models.Model):
    transaction = models.OneToOneField(Transaction, on_delete=models.PROTECT, related_name='invoice')
    invoice_number = models.CharField(max_length=50, unique=True)
    generated_pdf = models.FileField(upload_to='invoices/', blank=True, null=True)
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"INV-{self.invoice_number}"

class RefundRequest(models.Model):
    transaction = models.OneToOneField(Transaction, on_delete=models.PROTECT, related_name='refund_request')
    reason = models.TextField()
    refund_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    admin_notes = models.TextField(blank=True, null=True)
    processed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"REFUND-{self.transaction.id} | {self.refund_status}"
