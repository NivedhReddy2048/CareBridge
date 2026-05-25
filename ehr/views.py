from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from .models import EHRRecord, DocumentAttachment, AuditLog, AppointmentEHRLink
from .forms import EHRRecordForm, DocumentAttachmentForm

@login_required
def upload_ehr(request):
    if request.user.role != 'patient':
        return JsonResponse({"error": "Unauthorized"}, status=403)
        
    if request.method == 'POST':
        record_form = EHRRecordForm(request.POST)
        attachment_form = DocumentAttachmentForm(request.POST, request.FILES)
        
        if record_form.is_valid() and attachment_form.is_valid():
            record = record_form.save(commit=False)
            record.patient = request.user
            record.save()
            
            attachment = attachment_form.save(commit=False)
            attachment.ehr_record = record
            if hasattr(attachment.file, 'content_type'):
                attachment.file_type = attachment.file.content_type
            attachment.save()
            
            AuditLog.objects.create(
                user=request.user,
                ehr_record=record,
                action="UPLOADED_RECORD",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            # If AJAX request
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({"status": "success", "message": "Record uploaded successfully."})
                
            messages.success(request, "Health record uploaded successfully.")
            return redirect('patient_dashboard')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({"status": "error", "errors": record_form.errors}, status=400)
    
    # Not returning a full HTML template, just the JSON or a basic redirect for now
    return redirect('patient_dashboard')

@login_required
def view_ehr_document(request, attachment_id):
    attachment = get_object_or_404(DocumentAttachment, id=attachment_id)
    record = attachment.ehr_record
    
    # 1. Check if patient owns it
    has_access = False
    if request.user == record.patient:
        has_access = True
    # 2. Check if doctor is authorized
    elif request.user.role == 'doctor':
        # See if there's an appointment link
        has_access = AppointmentEHRLink.objects.filter(
            ehr_record=record,
            appointment__doctor__user=request.user,
            doctor_permission_granted=True
        ).exists()
        
    if not has_access:
        AuditLog.objects.create(
            user=request.user,
            ehr_record=record,
            action="UNAUTHORIZED_ACCESS_ATTEMPT",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        return HttpResponse("Unauthorized", status=403)
        
    AuditLog.objects.create(
        user=request.user,
        ehr_record=record,
        action="VIEWED_DOCUMENT",
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    # Serve file locally (Fallback for now, in prod this would redirect to an S3 presigned URL)
    response = HttpResponse(attachment.file.read(), content_type=attachment.file_type or 'application/octet-stream')
    response['Content-Disposition'] = f'inline; filename="{attachment.file.name}"'
    return response

@login_required
def link_ehr_to_appointment(request, appointment_id):
    if request.method == 'POST' and request.user.role == 'patient':
        ehr_ids = request.POST.getlist('ehr_ids')
        for eid in ehr_ids:
            ehr = get_object_or_404(EHRRecord, id=eid, patient=request.user)
            AppointmentEHRLink.objects.get_or_create(
                appointment_id=appointment_id,
                ehr_record=ehr
            )
        return JsonResponse({"status": "success"})
    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required
def ehr_dashboard(request):
    if request.user.role != 'patient':
        return redirect('doctor_dashboard')
        
    records = EHRRecord.objects.filter(patient=request.user).prefetch_related(
        'attachments__ai_analysis'
    ).order_by('-date_of_record', '-created_at')
    
    return render(request, 'ehr/ehr_dashboard.html', {
        'records': records
    })

@login_required
def delete_ehr(request, record_id):
    if request.user.role != 'patient':
        return JsonResponse({"error": "Unauthorized"}, status=403)
        
    record = get_object_or_404(EHRRecord, id=record_id, patient=request.user)
    record.delete()
    messages.success(request, "Record deleted successfully.")
    return redirect('ehr_dashboard')

@login_required
def reprocess_ehr(request, record_id):
    if not request.user.is_staff and request.user.role != 'doctor':
        # Patients might also want to trigger reprocess if it failed, but let's allow it for demonstration
        pass
        
    record = get_object_or_404(EHRRecord, id=record_id)
    attachment = record.attachments.first()
    if attachment:
        # Trigger Celery task synchronously for now if always eager is set, or async
        from intelligence.tasks import process_ehr_document
        process_ehr_document.delay(attachment.id)
        messages.success(request, "Document queued for re-analysis via OCR pipeline.")
    else:
        messages.error(request, "No document attached to reprocess.")
        
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('ehr_dashboard')
