"""
System-level tests for payment webhooks and duplicate prevention.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
import json
from unittest.mock import patch

from apps.articles.models import Article
from apps.articles.workflow import ArticleStatus
from apps.journals.models import Journal
from apps.payments.models import Invoice, Payment

User = get_user_model()


class PaymentWebhookTests(TestCase):
    """Test payment webhook handlers and duplicate prevention."""
    
    def setUp(self):
        self.client = APIClient()
        
        self.author = User.objects.create_user(
            email='author@example.com',
            username='author',
            password='pass123',
            role='AUTHOR'
        )
        
        self.journal = Journal.objects.create(
            name='Test Journal',
            issn='1234-5678',
            scope='Test',
            apc_enabled=True,
            apc_amount=500.00,
            currency='USD'
        )
        
        self.article = Article.objects.create(
            submission_id='SUB-001',
            title='Test Article',
            abstract='Test abstract',
            corresponding_author=self.author,
            journal=self.journal,
            status=ArticleStatus.ACCEPTED.value
        )
        
        self.invoice = Invoice.objects.create(
            article=self.article,
            amount=500.00,
            currency='USD',
            status=Invoice.Status.PENDING
        )
    
    def test_payme_webhook_creates_payment(self):
        """Test that Payme webhook creates payment record."""
        webhook_data = {
            'transaction_id': 'TXN123456',
            'invoice_number': self.invoice.invoice_number,
            'amount': '500.00',
            'status': 'paid'
        }
        
        # Mock signature verification
        with patch('apps.payments.webhooks.verify_payme_signature', return_value=True):
            response = self.client.post(
                '/api/payments/webhooks/payme/',
                data=json.dumps(webhook_data),
                content_type='application/json',
                HTTP_X_PAYME_SIGNATURE='valid_signature'
            )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check payment was created
        payment = Payment.objects.filter(provider_transaction_id='TXN123456').first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.status, 'COMPLETED')
        
        # Check invoice was updated
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, Invoice.Status.PAID)
    
    def test_duplicate_webhook_idempotent(self):
        """Test that duplicate webhooks are handled idempotently."""
        webhook_data = {
            'transaction_id': 'TXN123456',
            'invoice_number': self.invoice.invoice_number,
            'amount': '500.00',
            'status': 'paid'
        }
        
        # Mock signature verification
        with patch('apps.payments.webhooks.verify_payme_signature', return_value=True):
            # First webhook
            response1 = self.client.post(
                '/api/payments/webhooks/payme/',
                data=json.dumps(webhook_data),
                content_type='application/json',
                HTTP_X_PAYME_SIGNATURE='valid_signature'
            )
            
            # Duplicate webhook
            response2 = self.client.post(
                '/api/payments/webhooks/payme/',
                data=json.dumps(webhook_data),
                content_type='application/json',
                HTTP_X_PAYME_SIGNATURE='valid_signature'
            )
        
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data['status'], 'already_processed')
        
        # Should only have one payment record
        payments = Payment.objects.filter(provider_transaction_id='TXN123456')
        self.assertEqual(payments.count(), 1)
    
    def test_webhook_invalid_signature_rejected(self):
        """Test that webhooks with invalid signatures are rejected."""
        webhook_data = {
            'transaction_id': 'TXN123456',
            'invoice_number': self.invoice.invoice_number,
            'amount': '500.00',
            'status': 'paid'
        }
        
        # Mock signature verification to return False
        with patch('apps.payments.webhooks.verify_payme_signature', return_value=False):
            response = self.client.post(
                '/api/payments/webhooks/payme/',
                data=json.dumps(webhook_data),
                content_type='application/json',
                HTTP_X_PAYME_SIGNATURE='invalid_signature'
            )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Payment should not be created
        payment = Payment.objects.filter(provider_transaction_id='TXN123456').first()
        self.assertIsNone(payment)
    
    def test_webhook_updates_article_status(self):
        """Test that webhook updates article status to PAID."""
        self.article.status = ArticleStatus.PAYMENT_PENDING.value
        self.article.save()
        
        webhook_data = {
            'transaction_id': 'TXN123456',
            'invoice_number': self.invoice.invoice_number,
            'amount': '500.00',
            'status': 'paid'
        }
        
        with patch('apps.payments.webhooks.verify_payme_signature', return_value=True):
            response = self.client.post(
                '/api/payments/webhooks/payme/',
                data=json.dumps(webhook_data),
                content_type='application/json',
                HTTP_X_PAYME_SIGNATURE='valid_signature'
            )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Article status should be updated
        self.article.refresh_from_db()
        self.assertEqual(self.article.status, ArticleStatus.PAID.value)
    
    def test_click_webhook_same_behavior(self):
        """Test that Click webhook behaves the same as Payme."""
        webhook_data = {
            'transaction_id': 'CLICK123456',
            'invoice_number': self.invoice.invoice_number,
            'amount': '500.00',
            'status': 'paid'
        }
        
        with patch('apps.payments.webhooks.verify_click_signature', return_value=True):
            response = self.client.post(
                '/api/payments/webhooks/click/',
                data=json.dumps(webhook_data),
                content_type='application/json',
                HTTP_X_CLICK_SIGNATURE='valid_signature'
            )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        payment = Payment.objects.filter(provider_transaction_id='CLICK123456').first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.provider, 'CLICK')

