"""
Public URLs for certificate verification.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CertificateVerificationViewSet

router = DefaultRouter()
router.register(r'', CertificateVerificationViewSet, basename='certificate-verification')

urlpatterns = router.urls
