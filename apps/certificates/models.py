"""
Certificate models.
"""
from django.db import models
from django.core.exceptions import ValidationError
import uuid


class Certificate(models.Model):
    """
    Certificate model for published articles.
    
    Business rule: Certificate issued only after publication.
    """
    
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        REVOKED = 'REVOKED', 'Revoked'
    
    certificate_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text='Unique certificate identifier for verification'
    )
    article = models.OneToOneField(
        'articles.Article',
        on_delete=models.CASCADE,
        related_name='certificate'
    )
    
    # PDF File
    pdf_file = models.FileField(
        upload_to='certificates/',
        blank=True,
        null=True,
        help_text='Generated PDF certificate'
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    
    # Metadata
    issued_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(blank=True, null=True)
    revoked_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='revoked_certificates',
        limit_choices_to={'role': 'ADMIN'}
    )
    revocation_reason = models.TextField(blank=True)
    
    class Meta:
        db_table = 'certificates'
        ordering = ['-issued_at']
        indexes = [
            models.Index(fields=['certificate_id']),
            models.Index(fields=['status']),
            models.Index(fields=['article']),
        ]
    
    def __str__(self):
        return f"Certificate {self.certificate_id} - {self.article.submission_id}"
    
    def clean(self):
        """Validate business rules."""
        # Business rule: Certificate only after publication
        if self.article.status != 'PUBLISHED' and self.article.status != 'CERTIFICATE_ISSUED':
            raise ValidationError(
                "Certificate can only be issued for published articles."
            )
    
    def save(self, *args, **kwargs):
        """Override save to enforce business rules."""
        self.clean()
        super().save(*args, **kwargs)
    
    def revoke(self, user, reason=''):
        """
        Revoke certificate (Admin only).
        
        Args:
            user: Admin user revoking the certificate
            reason: Reason for revocation
        """
        if user.role != 'ADMIN':
            raise ValidationError("Only admins can revoke certificates.")
        
        self.status = self.Status.REVOKED
        from django.utils import timezone
        self.revoked_at = timezone.now()
        self.revoked_by = user
        self.revocation_reason = reason
        self.save()
        
        # Log revocation
        from apps.audit.models import AuditLog
        AuditLog.objects.create(
            actor=user,
            action='CERTIFICATE_REVOKED',
            entity_type='CERTIFICATE',
            entity_id=self.id,
            metadata={
                'certificate_id': str(self.certificate_id),
                'article_submission_id': self.article.submission_id,
                'reason': reason
            }
        )
    
    @property
    def verification_url(self):
        """Get public verification URL."""
        from django.conf import settings
        base_url = settings.CERTIFICATE_VERIFICATION_BASE_URL
        return f"{base_url}/{self.certificate_id}"

