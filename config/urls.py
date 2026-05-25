from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts import views as account_views # <--- Import this

urlpatterns = [
    # 1. THIS IS THE KEY: Point root ('') to the home_view, NOT RedirectView
    path('', account_views.home_view, name='home'),

    path('admin/', admin.site.urls),
    
    # Apps
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('appointments/', include('appointments.urls')),
    path('records/', include('records.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('billing/', include('billing.urls')),
    path('ehr/', include('ehr.urls')),
    path('api/v1/', include('api.v1.urls')),
    path('analytics/', include('analytics.urls')),
    path('enterprise/', include('enterprise.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
