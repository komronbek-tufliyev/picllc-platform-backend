"""
Audit logging models.
"""
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class AuditLog(models.Model):
    """
    Audit log for tracking all critical actions.
    
    Logs:
    - Status changes
    - Review decisions
    - Payment confirmations
    - Certificate issuance/revocation
    - Admin overrides
    """
    
    class ActionType(models.TextChoices):
        STATUS_CHANGE = 'STATUS_CHANGE', 'Status Change'
        REVIEW_SUBMITTED = 'REVIEW_SUBMITTED', 'Review Submitted'
        PAYMENT_CONFIRMED = 'PAYMENT_CONFIRMED', 'Payment Confirmed'
        CERTIFICATE_ISSUED = 'CERTIFICATE_ISSUED', 'Certificate Issued'
        CERTIFICATE_REVOKED = 'CERTIFICATE_REVOKED', 'Certificate Revoked'
        ADMIN_OVERRIDE = 'ADMIN_OVERRIDE', 'Admin Override'
        ARTICLE_SUBMITTED = 'ARTICLE_SUBMITTED', 'Article Submitted'
        ARTICLE_PUBLISHED = 'ARTICLE_PUBLISHED', 'Article Published'
    
    # Actor
    actor = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        help_text='User who performed the action (null for system actions)'
    )
    
    # Action
    action = models.CharField(
        max_length=50,
        choices=ActionType.choices
    )
    
    # Entity (Generic Foreign Key)
    entity_type = models.CharField(
        max_length=50,
        help_text='Type of entity (ARTICLE, INVOICE, CERTIFICATE, etc.)'
    )
    entity_id = models.PositiveIntegerField(
        help_text='ID of the entity'
    )
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        help_text='Additional action metadata'
    )
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['actor']),
            models.Index(fields=['action']),
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        actor_name = self.actor.email if self.actor else 'SYSTEM'
        return f"{actor_name} - {self.action} - {self.entity_type}#{self.entity_id}"

