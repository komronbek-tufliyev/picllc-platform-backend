"""
API views for payments.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .models import Invoice, Payment
from .serializers import (
    InvoiceSerializer,
    InvoiceListSerializer,
    PaymentInitSerializer
)
from apps.accounts.permissions import IsAuthor, IsAdmin, IsReviewerOrAdmin
from apps.articles.models import Article


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for invoices.
    
    - Authors: Can view their own invoices
    - Reviewers/Admins: Can view all invoices
    """
    queryset = Invoice.objects.select_related('article').prefetch_related('payments').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_provider']
    search_fields = ['invoice_number', 'article__submission_id', 'article__title']
    ordering_fields = ['created_at', 'paid_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return InvoiceListSerializer
        return InvoiceSerializer
    
    def get_queryset(self):
        """Filter based on user role."""
        user = self.request.user
        
        if user.role == 'AUTHOR':
            # Authors see only invoices for their articles
            return self.queryset.filter(article__corresponding_author=user)
        elif user.role in ['REVIEWER', 'ADMIN']:
            # Reviewers and admins see all invoices
            return self.queryset
        
        return Invoice.objects.none()
    
    @extend_schema(
        summary="Initiate payment for invoice",
        description="""
        Prepare external payment session (Payme/Click).
        
        **Important:** This endpoint does NOT change:
        - `Article.status` (remains unchanged)
        - `Article.payment_status` (remains unchanged)
        - `Invoice.status` (remains unchanged)
        
        It only returns a payment URL for redirecting the user to the payment provider.
        Payment status changes occur only when payment is confirmed via webhook or `mark_as_paid`.
        """,
        request=PaymentInitSerializer,
        responses={
            200: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "Initiate Payme payment",
                value={"provider": "PAYME", "return_url": "https://frontend.example.com/payment/success"},
                request_only=True,
            ),
            OpenApiExample(
                "Payment URL response",
                value={
                    "payment_url": "https://payme.example.com/pay/INV-ABC123DEF456",
                    "invoice_number": "INV-ABC123DEF456",
                    "amount": "500.00",
                    "currency": "USD"
                },
                response_only=True,
            ),
        ],
    )
    @action(detail=True, methods=['post'], serializer_class=PaymentInitSerializer)
    def initiate_payment(self, request, pk=None):
        """Initiate payment for invoice."""
        invoice = self.get_object()
        
        # Check permissions
        if request.user.role == 'AUTHOR':
            if invoice.article.corresponding_author != request.user:
                return Response(
                    {'error': 'You can only pay for your own invoices.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        serializer = PaymentInitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        provider = serializer.validated_data['provider']
        
        # TODO: Integrate with Payme/Click APIs
        # For now, return mock payment URL
        return Response({
            'payment_url': f'/mock-payment/{provider}/{invoice.invoice_number}',
            'invoice_number': invoice.invoice_number,
            'amount': str(invoice.amount),
            'currency': invoice.currency
        })
    
    @extend_schema(
        summary="Mark invoice as paid (Admin only)",
        description="""
        Manually mark invoice as paid (Admin override).
        
        **Side Effects:**
        - `Invoice.status` → `PAID`
        - `Article.payment_status` → `PAID`
        - **Important**: `Article.status` is **NOT modified** (remains `ACCEPTED`)
        
        This allows the article to proceed to production/publication (payment gate satisfied).
        """,
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'provider_transaction_id': {'type': 'string', 'example': 'MANUAL-123'},
                    'payment_provider': {'type': 'string', 'example': 'MANUAL'},
                },
            }
        },
        responses={
            200: InvoiceSerializer,
            403: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "Mark as paid",
                value={
                    "provider_transaction_id": "MANUAL-123",
                    "payment_provider": "MANUAL"
                },
                request_only=True,
            ),
        ],
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def mark_as_paid(self, request, pk=None):
        """Mark invoice as paid (Admin override)."""
        invoice = self.get_object()
        
        provider_transaction_id = request.data.get('provider_transaction_id', 'MANUAL')
        payment_provider = request.data.get('payment_provider')
        
        invoice.mark_as_paid(
            provider_transaction_id=provider_transaction_id,
            payment_provider=payment_provider,
            user=request.user
        )
        
        return Response(
            InvoiceSerializer(invoice).data,
            status=status.HTTP_200_OK
        )

