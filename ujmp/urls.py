"""
URL configuration for UJMP project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView
)
from apps.core.views import (
    health_check,
    health_check_liveness,
    health_check_readiness
)


urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Health check endpoints (Actuator-style)
    path('health/', health_check, name='health'),
    path('health/live/', health_check_liveness, name='health_live'),
    path('health/ready/', health_check_readiness, name='health_ready'),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API Endpoints
    path('api/auth/', include('apps.accounts.urls')),
    path('api/journals/', include('apps.journals.urls')),
    path('api/articles/', include('apps.articles.urls')),
    path('api/payments/', include('apps.payments.urls')),
    path('api/certificates/', include('apps.certificates.urls')),
    path('api/audit/', include('apps.audit.urls')),
    path('verify/certificate/', include('apps.certificates.public_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

