from django.urls import path
from . import views

app_name = 'enterprise'

urlpatterns = [
    path('login/', views.enterprise_login_view, name='enterprise_login'),
    path('', views.dashboard, name='dashboard'),
    path('analytics/', views.analytics, name='analytics'),
    path('ai-monitoring/', views.ai_monitoring, name='ai_monitoring'),
    path('ocr-monitoring/', views.ocr_monitoring, name='ocr_monitoring'),
    path('revenue/', views.revenue, name='revenue'),
    path('users/', views.user_management, name='user_management'),
    path('doctors/', views.doctor_approvals, name='doctor_approvals'),
    path('audit-logs/', views.audit_logs, name='audit_logs'),
    path('realtime/', views.realtime_monitoring, name='realtime_monitoring'),
    path('ai-engine/', views.ai_engine_dashboard, name='ai_engine_dashboard'),
    path('storage-monitoring/', views.storage_monitoring, name='storage_monitoring'),
    path('system-monitoring/', views.system_monitoring, name='system_monitoring'),
    path('telemedicine/', views.telemedicine_monitoring, name='telemedicine_monitoring'),
]
