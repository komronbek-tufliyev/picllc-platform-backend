"""
URLs for certificates.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CertificateViewSet

router = DefaultRouter()
router.register(r'', CertificateViewSet, basename='certificate')

urlpatterns = router.urls
