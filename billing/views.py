import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .services.payment_service import PaymentService
from .services.webhook_service import WebhookService
from .models import Invoice, Transaction
import logging

logger = logging.getLogger(__name__)

@login_required
def create_payment_session(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    try:
        data = json.loads(request.body)
        appointment_id = data.get("appointment_id")
        
        if not appointment_id:
            return JsonResponse({"error": "Appointment ID required"}, status=400)
            
        service = PaymentService()
        checkout_data = service.create_checkout_session(request.user, appointment_id)
        
        return JsonResponse(checkout_data)
        
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        return JsonResponse({"error": "Server error"}, status=500)

@login_required
def verify_payment(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
        
    try:
        data = json.loads(request.body)
        order_id = data.get("razorpay_order_id")
        payment_id = data.get("razorpay_payment_id")
        signature = data.get("razorpay_signature")
        
        service = PaymentService()
        txn = service.verify_and_confirm_payment(order_id, payment_id, signature)
        
        return JsonResponse({"status": "success", "transaction_id": txn.id})
        
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error verifying payment: {str(e)}")
        return JsonResponse({"error": "Server error"}, status=500)

@csrf_exempt
def razorpay_webhook(request):
    if request.method != "POST":
        return HttpResponse(status=405)
        
    try:
        payload = request.body
        signature = request.headers.get('X-Razorpay-Signature')
        
        service = WebhookService()
        
        if not service.verify_webhook_signature(payload, signature):
            return HttpResponse(status=400)
            
        event_data = json.loads(payload)
        service.process_webhook(event_data)
        
        return HttpResponse(status=200)
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return HttpResponse(status=500)

@login_required
def payment_success(request):
    txn_id = request.GET.get('txn_id')
    txn = get_object_or_404(Transaction, id=txn_id, patient=request.user)
    
    return render(request, 'billing/payment_success.html', {'transaction': txn})

import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

@login_required
def download_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    # Ensure only patient or admin can download
    if invoice.transaction.patient != request.user and request.user.role != 'admin':
        return JsonResponse({"error": "Unauthorized"}, status=403)
        
    try:
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Header
        p.setFont("Helvetica-Bold", 20)
        p.drawString(100, 750, "CareBridge Healthcare")
        
        p.setFont("Helvetica", 12)
        p.drawString(100, 720, "Official Invoice & Receipt")
        p.line(100, 710, 500, 710)
        
        # Details
        p.setFont("Helvetica-Bold", 12)
        p.drawString(100, 680, f"Invoice Number: {invoice.invoice_number}")
        p.setFont("Helvetica", 12)
        p.drawString(100, 660, f"Date: {invoice.generated_at.strftime('%Y-%m-%d %H:%M')}")
        p.drawString(100, 640, f"Patient: {invoice.transaction.patient.first_name} {invoice.transaction.patient.last_name}")
        p.drawString(100, 620, f"Doctor: {invoice.transaction.appointment.doctor.user.first_name} {invoice.transaction.appointment.doctor.user.last_name}")
        
        # Amount
        p.setFont("Helvetica-Bold", 14)
        p.drawString(100, 580, f"Total Amount Paid: INR {invoice.total_amount}")
        
        p.setFont("Helvetica", 10)
        p.drawString(100, 560, f"Transaction ID: {invoice.transaction.razorpay_payment_id or 'N/A'}")
        
        # Footer
        p.setFont("Helvetica-Oblique", 10)
        p.drawString(100, 100, "Thank you for trusting CareBridge. This is a computer-generated document.")
        
        p.showPage()
        p.save()
        buffer.seek(0)
        
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="carebridge_{invoice.invoice_number}.pdf"'
        return response
    except Exception as e:
        logger.error(f"Failed to generate PDF for invoice {invoice_id}: {str(e)}")
        return HttpResponse("Error generating PDF invoice. Please contact support.", status=500)
