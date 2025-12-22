"""
Serializers for payments.
"""
from rest_framework import serializers
from .models import Invoice, Payment
from apps.articles.serializers import ArticleListSerializer


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment."""
    
    class Meta:
        model = Payment
        fields = [
            'id', 'provider', 'provider_transaction_id', 'amount', 'currency',
            'status', 'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_at']


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for Invoice."""
    article = ArticleListSerializer(read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'article', 'amount', 'currency',
            'status', 'payment_provider', 'provider_transaction_id',
            'created_at', 'updated_at', 'paid_at', 'payments'
        ]
        read_only_fields = [
            'id', 'invoice_number', 'created_at', 'updated_at', 'paid_at'
        ]


class InvoiceListSerializer(serializers.ModelSerializer):
    """Simplified serializer for invoice lists."""
    article_title = serializers.CharField(source='article.title', read_only=True)
    article_submission_id = serializers.CharField(source='article.submission_id', read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'article_submission_id', 'article_title',
            'amount', 'currency', 'status', 'payment_provider', 'created_at', 'paid_at'
        ]


class PaymentInitSerializer(serializers.Serializer):
    """Serializer for initiating payment."""
    provider = serializers.ChoiceField(choices=['PAYME', 'CLICK'])
    return_url = serializers.URLField(required=False)

