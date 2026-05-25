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
