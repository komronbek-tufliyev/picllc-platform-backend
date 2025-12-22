"""
Webhook handlers for payment providers.
"""
import hmac
import hashlib
import json
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Invoice, Payment
from apps.articles.throttling import WebhookRateThrottle


def verify_payme_signature(data, signature):
    """Verify Payme webhook signature."""
    secret_key = settings.PAYME_SECRET_KEY
    if not secret_key:
        return False
    
    # Payme signature verification logic
    # This is a placeholder - actual implementation depends on Payme API docs
    expected_signature = hmac.new(
        secret_key.encode(),
        json.dumps(data, sort_keys=True).encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)


def verify_click_signature(data, signature):
    """Verify Click webhook signature."""
    secret_key = settings.CLICK_SECRET_KEY
    if not secret_key:
        return False
    
    # Click signature verification logic
    # This is a placeholder - actual implementation depends on Click API docs
    expected_signature = hmac.new(
        secret_key.encode(),
        json.dumps(data, sort_keys=True).encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)


@method_decorator(csrf_exempt, name='dispatch')
class PaymeWebhookView(APIView):
    """Webhook endpoint for Payme payment notifications."""
    throttle_classes = [WebhookRateThrottle]
    
    def post(self, request):
        """Handle Payme webhook."""
        try:
            data = json.loads(request.body)
            signature = request.headers.get('X-Payme-Signature', '')
            
            # Verify signature
            if not verify_payme_signature(data, signature):
                return Response(
                    {'error': 'Invalid signature'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Extract payment information
            transaction_id = data.get('transaction_id')
            invoice_number = data.get('invoice_number')  # Should be passed during payment initiation
            amount = data.get('amount')
            status_code = data.get('status')  # 'paid', 'failed', etc.
            
            if not transaction_id or not invoice_number:
                return Response(
                    {'error': 'Missing required fields'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get invoice
            try:
                invoice = Invoice.objects.get(invoice_number=invoice_number)
            except Invoice.DoesNotExist:
                return Response(
                    {'error': 'Invoice not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if payment already processed (idempotency)
            existing_payment = Payment.objects.filter(
                provider_transaction_id=transaction_id
            ).first()
            
            if existing_payment:
                # Payment already processed
                return Response({'status': 'already_processed'})
            
            # Create payment record
            payment = Payment.objects.create(
                invoice=invoice,
                provider='PAYME',
                provider_transaction_id=transaction_id,
                amount=amount or invoice.amount,
                currency=invoice.currency,
                status='COMPLETED' if status_code == 'paid' else 'FAILED',
                webhook_data=data
            )
            
            # Update invoice if paid
            if status_code == 'paid' and invoice.status != Invoice.Status.PAID:
                invoice.mark_as_paid(
                    provider_transaction_id=transaction_id,
                    payment_provider='PAYME',
                    user=None  # System action
                )
            
            return Response({'status': 'success'})
            
        except json.JSONDecodeError:
            return Response(
                {'error': 'Invalid JSON'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class ClickWebhookView(APIView):
    """Webhook endpoint for Click payment notifications."""
    throttle_classes = [WebhookRateThrottle]
    
    def post(self, request):
        """Handle Click webhook."""
        try:
            data = json.loads(request.body)
            signature = request.headers.get('X-Click-Signature', '')
            
            # Verify signature
            if not verify_click_signature(data, signature):
                return Response(
                    {'error': 'Invalid signature'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Extract payment information
            transaction_id = data.get('transaction_id')
            invoice_number = data.get('invoice_number')
            amount = data.get('amount')
            status_code = data.get('status')
            
            if not transaction_id or not invoice_number:
                return Response(
                    {'error': 'Missing required fields'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get invoice
            try:
                invoice = Invoice.objects.get(invoice_number=invoice_number)
            except Invoice.DoesNotExist:
                return Response(
                    {'error': 'Invoice not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check idempotency
            existing_payment = Payment.objects.filter(
                provider_transaction_id=transaction_id
            ).first()
            
            if existing_payment:
                return Response({'status': 'already_processed'})
            
            # Create payment record
            payment = Payment.objects.create(
                invoice=invoice,
                provider='CLICK',
                provider_transaction_id=transaction_id,
                amount=amount or invoice.amount,
                currency=invoice.currency,
                status='COMPLETED' if status_code == 'paid' else 'FAILED',
                webhook_data=data
            )
            
            # Update invoice if paid
            if status_code == 'paid' and invoice.status != Invoice.Status.PAID:
                invoice.mark_as_paid(
                    provider_transaction_id=transaction_id,
                    payment_provider='CLICK',
                    user=None  # System action
                )
            
            return Response({'status': 'success'})
            
        except json.JSONDecodeError:
            return Response(
                {'error': 'Invalid JSON'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

