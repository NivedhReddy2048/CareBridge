from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Sum, Count
from django.utils.decorators import method_decorator

from .permissions import enterprise_admin_required
from accounts.models import CustomUser
from appointments.models import Appointment, Doctor
from billing.models import Transaction
from analytics.models import AIProcessingMetrics, ErrorEventLog, WebSocketConnectionMetrics, SystemHealthLog
from intelligence.models import AIAnalysisResult
from notifications.models import Notification, RealTimeEventLog
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from django.contrib import messages

def enterprise_login_view(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        next_url = request.POST.get('next', '/enterprise/')
        
        user = authenticate(request, username=u, password=p)
        if user is not None:
            # Check if user is an admin
            if user.is_superuser or getattr(user, 'role', '') == 'admin':
                login(request, user)
                return redirect(next_url)
            else:
                # User is valid but not an admin
                login(request, user)  # Login temporarily just to logout cleanly, or just don't login
                logout(request)
                messages.error(request, "Unauthorized enterprise access. Staff only.")
        else:
            messages.error(request, "Invalid credentials.")
            
    return render(request, 'enterprise/login.html')

@enterprise_admin_required
def dashboard(request):
    total_users = CustomUser.objects.count()
    active_doctors = Doctor.objects.filter(is_verified=True).count()
    total_patients = CustomUser.objects.filter(role='patient').count()
    appointments_today = Appointment.objects.count() # Would filter by today in real app
    
    total_ocr = AIProcessingMetrics.objects.count()
    ocr_fails = AIProcessingMetrics.objects.filter(is_success=False).count()
    ai_success_rate = round(((total_ocr - ocr_fails) / total_ocr * 100) if total_ocr > 0 else 0, 2)
    
    revenue = Transaction.objects.filter(payment_status='success').aggregate(Sum('amount'))['amount__sum'] or 0.0
    active_ws = WebSocketConnectionMetrics.objects.filter(disconnected_at__isnull=True).count()

    context = {
        'total_users': total_users,
        'active_doctors': active_doctors,
        'total_patients': total_patients,
        'appointments_today': appointments_today,
        'ai_success_rate': ai_success_rate,
        'ocr_fails': ocr_fails,
        'revenue': revenue,
        'active_ws': active_ws,
    }
    return render(request, 'enterprise/dashboard.html', context)

@enterprise_admin_required
def analytics(request):
    return render(request, 'analytics/admin_dashboard.html') # Reuse existing phase-6 dashboard inside the new layout if needed, or build new

@enterprise_admin_required
def ai_monitoring(request):
    results = AIAnalysisResult.objects.select_related('document').order_by('-processed_at')
    paginator = Paginator(results, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'enterprise/ai_monitoring.html', {'page_obj': page_obj})

@enterprise_admin_required
def ocr_monitoring(request):
    metrics = AIProcessingMetrics.objects.select_related('document').order_by('-start_time')
    paginator = Paginator(metrics, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'enterprise/ocr_monitoring.html', {'page_obj': page_obj})

@enterprise_admin_required
def revenue(request):
    transactions = Transaction.objects.select_related('patient', 'appointment').order_by('-created_at')
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'enterprise/revenue_dashboard.html', {'page_obj': page_obj})

@enterprise_admin_required
def user_management(request):
    users = CustomUser.objects.order_by('-date_joined')
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'enterprise/user_management.html', {'page_obj': page_obj})

@enterprise_admin_required
def doctor_approvals(request):
    doctors = Doctor.objects.select_related('user').order_by('-user__date_joined')
    paginator = Paginator(doctors, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'enterprise/doctor_approvals.html', {'page_obj': page_obj})

@enterprise_admin_required
def audit_logs(request):
    logs = ErrorEventLog.objects.order_by('-timestamp')
    paginator = Paginator(logs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'enterprise/audit_logs.html', {'page_obj': page_obj})

@enterprise_admin_required
def realtime_monitoring(request):
    events = RealTimeEventLog.objects.order_by('-created_at')[:50]
    return render(request, 'enterprise/realtime_monitoring.html', {'events': events})

from ai_engine.models import AIUsageLog, AIAuditLog
from django.db.models import Sum

@enterprise_admin_required
def ai_engine_dashboard(request):
    
    total_tokens = AIUsageLog.objects.aggregate(Sum('tokens_used'))['tokens_used__sum'] or 0
    total_calls = AIUsageLog.objects.count()
    success_calls = AIUsageLog.objects.filter(status='SUCCESS').count()
    fallback_calls = AIUsageLog.objects.filter(fallback_triggered=True).count()
    
    failure_rate = 0
    if total_calls > 0:
        failure_rate = round(((total_calls - success_calls) / total_calls) * 100, 2)
        
    fallback_rate = 0
    if total_calls > 0:
        fallback_rate = round((fallback_calls / total_calls) * 100, 2)
        
    avg_latency = 0
    if total_calls > 0:
        avg_latency = AIUsageLog.objects.aggregate(Sum('latency_ms'))['latency_ms__sum'] / total_calls
        
    # Get audit logs as well
    audit_logs_list = AIAuditLog.objects.order_by('-timestamp')
    audit_paginator = Paginator(audit_logs_list, 20)
    audit_page_number = request.GET.get('audit_page')
    audit_logs = audit_paginator.get_page(audit_page_number)
    
    logs_list = AIUsageLog.objects.order_by('-created_at')
    logs_paginator = Paginator(logs_list, 20)
    logs_page_number = request.GET.get('page')
    logs = logs_paginator.get_page(logs_page_number)
        
    return render(request, 'enterprise/ai_engine_dashboard.html', {
        'logs': logs,
        'audit_logs': audit_logs,
        'total_tokens': total_tokens,
        'total_calls': total_calls,
        'failure_rate': failure_rate,
        'fallback_rate': fallback_rate,
        'avg_latency': int(avg_latency)
    })

@enterprise_admin_required
def storage_monitoring(request):
    from ehr.models import DocumentAttachment, AuditLog
    from records.models import MalwareScanLog
    from django.db.models import Sum, Count

    # Total uploads
    total_uploads = DocumentAttachment.objects.count()

    # Storage consumed (sum of file sizes, approximation)
    # Since we can't efficiently sum file sizes across S3, we would ideally store size on DB.
    # For now, we will leave it as placeholder "Calculated async" or estimate it.
    storage_consumed_mb = 0

    # Scans
    infected_count = MalwareScanLog.objects.filter(status='INFECTED').count()
    failed_scans = MalwareScanLog.objects.filter(status='FAILED').count()

    # Recent downloads
    recent_downloads = AuditLog.objects.filter(action='DOWNLOADED_ATTACHMENT').order_by('-timestamp')[:50]

    # Top uploaders
    top_uploaders = DocumentAttachment.objects.values('ehr_record__patient__username').annotate(upload_count=Count('id')).order_by('-upload_count')[:10]

    context = {
        'total_uploads': total_uploads,
        'storage_consumed_mb': storage_consumed_mb,
        'infected_count': infected_count,
        'failed_scans': failed_scans,
        'recent_downloads': recent_downloads,
        'top_uploaders': top_uploaders
    }
    return render(request, 'enterprise/storage_monitoring.html', context)

@enterprise_admin_required
def system_monitoring(request):
    import os
    import psutil
    from django.db import connections
    from django.db.utils import OperationalError
    from django.core.cache import cache

    # Check DB
    db_status = "Healthy"
    try:
        c = connections['default'].cursor()
        c.execute("SELECT 1")
    except OperationalError:
        db_status = "Down"

    # Check Redis
    redis_status = "Healthy"
    try:
        cache.set('sys_health_check', 'ok', timeout=1)
        if cache.get('sys_health_check') != 'ok':
            redis_status = "Mismatch"
    except Exception:
        redis_status = "Down"

    # Check Celery
    celery_status = "Healthy"
    try:
        broker_url = os.environ.get('REDIS_URL')
        if not broker_url:
            celery_status = "Missing Config"
    except Exception:
        celery_status = "Down"

    # System Metrics
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    
    # Deployment metadata (rendered from env in render)
    render_service = os.environ.get("RENDER_SERVICE_NAME", "Local / Unknown")
    render_instance = os.environ.get("RENDER_INSTANCE_ID", "N/A")

    # Observability Metrics (approximations for dashboard)
    websocket_connections = cache.get('active_websockets', 0)
    queue_backlog = cache.get('celery_queue_backlog', 0)
    failed_tasks = cache.get('celery_failed_tasks', 0)
    api_rate_limit_hits = cache.get('api_rate_limit_hits', 0)

    context = {
        'db_status': db_status,
        'redis_status': redis_status,
        'celery_status': celery_status,
        'cpu_percent': cpu_percent,
        'memory_percent': memory_percent,
        'render_service': render_service,
        'render_instance': render_instance,
        'websocket_connections': websocket_connections,
        'queue_backlog': queue_backlog,
        'failed_tasks': failed_tasks,
        'api_rate_limit_hits': api_rate_limit_hits,
    }
    return render(request, 'enterprise/system_monitoring.html', context)

@enterprise_admin_required
def telemedicine_monitoring(request):
    from telemedicine.models import ConsultationSession, ConsultationEvent
    from django.db.models import Count
    
    active_sessions = ConsultationSession.objects.filter(status='IN_PROGRESS').count()
    completed_sessions = ConsultationSession.objects.filter(status='COMPLETED').count()
    failed_sessions = ConsultationSession.objects.filter(status='CANCELLED').count()
    
    recent_events = ConsultationEvent.objects.order_by('-timestamp')[:50]
    
    context = {
        'active_sessions': active_sessions,
        'completed_sessions': completed_sessions,
        'failed_sessions': failed_sessions,
        'recent_events': recent_events
    }
    return render(request, 'enterprise/telemedicine_monitoring.html', context)
