"""
Serializers for certificates.
"""
from rest_framework import serializers
from .models import Certificate
from apps.articles.serializers import ArticleListSerializer


class CertificateSerializer(serializers.ModelSerializer):
    """Serializer for Certificate."""
    article = ArticleListSerializer(read_only=True)
    verification_url = serializers.CharField(read_only=True)
    
    class Meta:
        model = Certificate
        fields = [
            'id', 'certificate_id', 'article', 'pdf_file', 'status',
            'issued_at', 'revoked_at', 'revoked_by', 'revocation_reason',
            'verification_url'
        ]
        read_only_fields = [
            'id', 'certificate_id', 'issued_at', 'revoked_at',
            'revoked_by', 'verification_url'
        ]


class CertificateListSerializer(serializers.ModelSerializer):
    """Simplified serializer for certificate lists."""
    article_title = serializers.CharField(source='article.title', read_only=True)
    article_submission_id = serializers.CharField(source='article.submission_id', read_only=True)
    
    class Meta:
        model = Certificate
        fields = [
            'id', 'certificate_id', 'article_submission_id', 'article_title',
            'status', 'issued_at', 'revoked_at'
        ]


class CertificateVerificationSerializer(serializers.Serializer):
    """Serializer for certificate verification response."""
    certificate_id = serializers.UUIDField()
    status = serializers.CharField()
    article_title = serializers.CharField()
    article_submission_id = serializers.CharField()
    journal_name = serializers.CharField()
    publication_date = serializers.DateField(allow_null=True)
    publication_url = serializers.URLField(allow_null=True)
    issued_at = serializers.DateTimeField()
    revoked = serializers.BooleanField()

