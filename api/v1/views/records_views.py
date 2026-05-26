from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.shortcuts import get_object_or_404, redirect
from django.core.cache import cache
from ehr.models import EHRRecord, DocumentAttachment, AuditLog

class SecureDownloadAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        record = get_object_or_404(EHRRecord, pk=pk)
        
        # 1. Access Control
        user = request.user
        
        is_owner = record.patient == user
        # Doctor check: Check if doctor has an appointment linked to this record
        is_assigned_doctor = getattr(user, 'role', None) == 'doctor' and record.appointment_links.filter(appointment__doctor__user=user).exists()
        is_admin = getattr(user, 'role', None) == 'admin' or user.is_staff
        
        if not (is_owner or is_assigned_doctor or is_admin):
            return Response({"error": "Unauthorized access"}, status=status.HTTP_403_FORBIDDEN)
            
        attachment = record.attachments.first()
            
        # 2. Check if file exists
        if not attachment or not attachment.file:
            return Response({"error": "No file attached to this record"}, status=status.HTTP_404_NOT_FOUND)
            
        # 3. Cache Optimization for presigned URLs
        cache_key = f"presigned_url_ehr_{record.id}"
        url = cache.get(cache_key)
        
        if not url:
            # Generate Presigned URL using underlying storage
            try:
                # If using S3, url() automatically generates presigned url if querystring_auth is True
                url = attachment.file.url
                
                # Cache for slightly less than expiration (e.g. 290 seconds if expire is 300)
                cache.set(cache_key, url, timeout=290)
            except Exception as e:
                return Response({"error": f"Failed to generate secure URL: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        # 4. Audit Logging
        AuditLog.objects.create(
            user=user,
            ehr_record=record,
            action='DOWNLOADED_ATTACHMENT',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return redirect(url)
