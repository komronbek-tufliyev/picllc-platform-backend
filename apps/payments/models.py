"""
Payment and invoice models.
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class Invoice(models.Model):
    """
    Invoice model for APC payments.
    
    Business rule: Invoice generated only after article is ACCEPTED.
    """
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PAID = 'PAID', 'Paid'
        FAILED = 'FAILED', 'Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        help_text='Unique invoice identifier'
    )
    article = models.OneToOneField(
        'articles.Article',
        on_delete=models.CASCADE,
        related_name='invoice'
    )
    
    # Amount
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(max_length=3, default='USD')
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Payment Provider
    payment_provider = models.CharField(
        max_length=20,
        choices=[
            ('PAYME', 'Payme'),
            ('CLICK', 'Click'),
        ],
        blank=True,
        null=True
    )
    provider_transaction_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Transaction ID from payment provider'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'invoices'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['status']),
            models.Index(fields=['article']),
        ]
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.article.submission_id}"
    
    def save(self, *args, **kwargs):
        """Generate invoice number if not set."""
        if not self.invoice_number:
            self.invoice_number = f"INV-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)
    
    def mark_as_paid(self, provider_transaction_id=None, payment_provider=None, user=None):
        """
        Mark invoice as paid.
        
        Business rule: This triggers article status transition to PAID.
        """
        if self.status == self.Status.PAID:
            return  # Already paid, idempotent
        
        self.status = self.Status.PAID
        if provider_transaction_id:
            self.provider_transaction_id = provider_transaction_id
        if payment_provider:
            self.payment_provider = payment_provider
        from django.utils import timezone
        self.paid_at = timezone.now()
        self.save()
        
        # Update article status
        article = self.article
        if article.status == 'PAYMENT_PENDING':
            article.transition_status(
                article.current_status_enum,
                'SYSTEM',
                user=user
            )
            # Manually set to PAID since transition_status might not handle this
            article.status = 'PAID'
            article.save()
        
        # Log payment
        if user:
            from apps.audit.models import AuditLog
            AuditLog.objects.create(
                actor=user if user else None,
                action='PAYMENT_CONFIRMED',
                entity_type='INVOICE',
                entity_id=self.id,
                metadata={
                    'invoice_number': self.invoice_number,
                    'amount': str(self.amount),
                    'currency': self.currency,
                    'provider': payment_provider or 'MANUAL',
                    'transaction_id': provider_transaction_id
                }
            )
        
        # Send email notification
        from apps.notifications.tasks import send_payment_confirmation_email
        send_payment_confirmation_email.delay(self.id)


class Payment(models.Model):
    """
    Payment transaction records.
    
    Stores individual payment attempts and webhook data.
    """
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    
    # Provider Information
    provider = models.CharField(
        max_length=20,
        choices=[
            ('PAYME', 'Payme'),
            ('CLICK', 'Click'),
        ]
    )
    provider_transaction_id = models.CharField(max_length=255, unique=True)
    
    # Amount (may differ from invoice if partial payment)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(max_length=3)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('COMPLETED', 'Completed'),
            ('FAILED', 'Failed'),
            ('CANCELLED', 'Cancelled'),
        ],
        default='PENDING'
    )
    
    # Webhook data
    webhook_data = models.JSONField(
        default=dict,
        help_text='Raw webhook payload from payment provider'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['provider_transaction_id']),
            models.Index(fields=['status']),
            models.Index(fields=['invoice']),
        ]
    
    def __str__(self):
        return f"Payment {self.provider_transaction_id} - {self.invoice.invoice_number}"

