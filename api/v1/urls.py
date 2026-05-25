from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from api.v1.views.auth_views import CustomTokenObtainPairView
from api.v1.views.ehr_views import EHRViewSet
from api.v1.views.appointment_views import AppointmentViewSet, DoctorViewSet
from api.v1.views.billing_views import create_payment_session, verify_payment
from api.v1.views.notification_views import NotificationViewSet
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'ehr/records', EHRViewSet, basename='ehr')
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'doctors', DoctorViewSet, basename='doctor')
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    # Swagger Docs
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # JWT Authentication
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Viewsets (EHR, Appointments)
    path('', include(router.urls)),

    # Custom Action routes mapping
    path('ehr/upload/', EHRViewSet.as_view({'post': 'upload'}), name='api-ehr-upload'),
    path('ehr/ai-summary/<int:pk>/', EHRViewSet.as_view({'get': 'ai_summary'}), name='api-ehr-ai-summary'),
    path('appointments/book/', AppointmentViewSet.as_view({'post': 'book'}), name='api-appointments-book'),
    
    # Billing
    path('billing/create-order/', create_payment_session, name='api-billing-create-order'),
    path('billing/verify-payment/', verify_payment, name='api-billing-verify-payment'),
]
