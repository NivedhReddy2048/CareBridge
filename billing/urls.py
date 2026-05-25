from django.urls import path
from . import views

urlpatterns = [
    path('api/create-session/', views.create_payment_session, name='create_payment_session'),
    path('api/verify-payment/', views.verify_payment, name='verify_payment'),
    path('webhook/razorpay/', views.razorpay_webhook, name='razorpay_webhook'),
    path('success/', views.payment_success, name='payment_success'),
    path('invoice/<int:invoice_id>/download/', views.download_invoice, name='download_invoice'),
]
