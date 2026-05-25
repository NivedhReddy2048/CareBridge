from django.db import models

class PaymentStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    PROCESSING = 'PROCESSING', 'Processing'
    SUCCESS = 'SUCCESS', 'Success'
    FAILED = 'FAILED', 'Failed'
    REFUNDED = 'REFUNDED', 'Refunded'
    CANCELLED = 'CANCELLED', 'Cancelled'
    EXPIRED = 'EXPIRED', 'Expired'

class PaymentMethod(models.TextChoices):
    RAZORPAY = 'RAZORPAY', 'Razorpay'
    STRIPE = 'STRIPE', 'Stripe'
    CASH = 'CASH', 'Cash'
