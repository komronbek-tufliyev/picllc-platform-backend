"""
URL configuration for UJMP project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView
)


def health_check(request):
    """Health check endpoint for Docker/load balancer."""
    return JsonResponse({'status': 'healthy'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health'),
    
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

