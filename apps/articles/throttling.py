"""
Rate limiting/throttling for article endpoints.
"""
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.core.cache import cache
from django.conf import settings


class ArticleSubmissionThrottle(UserRateThrottle):
    """Throttle article submissions."""
    scope = 'article_submission'
    rate = '5/hour'  # 5 submissions per hour per user


class ArticleWorkflowThrottle(UserRateThrottle):
    """Throttle workflow actions."""
    scope = 'workflow_action'
    rate = '20/hour'  # 20 actions per hour per user


class PublicAPIRateThrottle(AnonRateThrottle):
    """Throttle public API endpoints."""
    scope = 'public_api'
    rate = '100/hour'  # 100 requests per hour per IP


class WebhookRateThrottle(AnonRateThrottle):
    """Throttle webhook endpoints."""
    scope = 'webhook'
    rate = '1000/hour'  # 1000 requests per hour per IP (webhooks can be frequent)


class CertificateVerificationThrottle(AnonRateThrottle):
    """Throttle certificate verification."""
    scope = 'certificate_verification'
    rate = '60/minute'  # 60 verifications per minute per IP

