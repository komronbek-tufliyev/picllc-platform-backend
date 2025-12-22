"""
URLs for payments.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InvoiceViewSet
from .webhooks import PaymeWebhookView, ClickWebhookView

router = DefaultRouter()
router.register(r'invoices', InvoiceViewSet, basename='invoice')

urlpatterns = [
    path('webhooks/payme/', PaymeWebhookView.as_view(), name='payme-webhook'),
    path('webhooks/click/', ClickWebhookView.as_view(), name='click-webhook'),
] + router.urls
