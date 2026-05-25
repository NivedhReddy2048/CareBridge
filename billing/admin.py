from django.contrib import admin
from .models import Transaction, Invoice, RefundRequest

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'amount', 'currency', 'payment_status', 'created_at')
    list_filter = ('payment_status', 'payment_method', 'created_at')
    search_fields = ('razorpay_order_id', 'razorpay_payment_id', 'patient__username')
    readonly_fields = ('created_at', 'updated_at', 'completed_at', 'refunded_at')

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'transaction', 'total_amount', 'generated_at')
    search_fields = ('invoice_number', 'transaction__razorpay_order_id')
    readonly_fields = ('generated_at',)

@admin.register(RefundRequest)
class RefundRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'transaction', 'refund_status', 'processed_at')
    list_filter = ('refund_status',)
