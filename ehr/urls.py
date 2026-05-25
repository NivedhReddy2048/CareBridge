from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_ehr, name='upload_ehr'),
    path('document/<int:attachment_id>/', views.view_ehr_document, name='view_ehr_document'),
    path('link-appointment/<int:appointment_id>/', views.link_ehr_to_appointment, name='link_ehr_to_appointment'),
    path('dashboard/', views.ehr_dashboard, name='ehr_dashboard'),
    path('delete/<int:record_id>/', views.delete_ehr, name='delete_ehr'),
    path('reprocess/<int:record_id>/', views.reprocess_ehr, name='reprocess_ehr'),
]
