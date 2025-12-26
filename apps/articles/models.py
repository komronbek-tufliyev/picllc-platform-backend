"""
Article models with strict workflow state machine.
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime
import string
import random
from .workflow import (
    ArticleStatus,
    can_transition,
    can_publish,
    can_issue_certificate
)


def generate_submission_id() -> str:
    """
    Generate unique submission identifier.
    Format: SUB-YYYYMMDD-XXXXXX (e.g., SUB-20240115-A3B2C1)
    """
    date_str = datetime.now().strftime('%Y%m%d')
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"SUB-{date_str}-{random_suffix}"


class Article(models.Model):
    """
    Article model with strict workflow state machine.
    
    Enforces:
    - Payment before publication
    - Certificate only after publication
    - Allowed state transitions only
    """
    
    # Basic Information
    submission_id = models.CharField(
        max_length=50,
        unique=True,
        help_text='Unique submission identifier'
    )
    title = models.CharField(max_length=500)
    abstract = models.TextField()
    keywords = models.CharField(max_length=500, blank=True)
    
    # Authors
    corresponding_author = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='authored_articles',
        limit_choices_to={'role': 'AUTHOR'}
    )
    authors = models.JSONField(
        default=list,
        help_text='List of authors with affiliations'
    )
    
    # Journal
    journal = models.ForeignKey(
        'journals.Journal',
        on_delete=models.PROTECT,
        related_name='articles'
    )
    
    # Workflow Status (Scientific Lifecycle)
    status = models.CharField(
        max_length=30,
        choices=[(status.value, status.name) for status in ArticleStatus],
        default=ArticleStatus.DRAFT.value
    )
    
    # Payment Status (Business Lifecycle)
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('NONE', 'None'),
            ('PENDING', 'Pending'),
            ('PAID', 'Paid'),
            ('NOT_REQUIRED', 'Not Required'),
        ],
        default='NONE',
        help_text='Payment status separate from article scientific workflow'
    )
    
    # Declarations
    ethics_declaration = models.BooleanField(default=False)
    originality_declaration = models.BooleanField(default=False)
    
    # Publication
    publication_url = models.URLField(blank=True, null=True)
    publication_date = models.DateField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'articles'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['submission_id']),
            models.Index(fields=['status']),
            models.Index(fields=['corresponding_author', 'status']),
            models.Index(fields=['journal', 'status']),
        ]
    
    def __str__(self):
        return f"{self.submission_id}: {self.title[:50]}"
    
    def clean(self):
        """Validate business rules."""
        # Validate status transitions will be handled in save() method
        pass
    
    def save(self, *args, **kwargs):
        """Override save to enforce workflow rules."""
        # Generate submission_id if not set
        if not self.submission_id:
            self.submission_id = generate_submission_id()
            # Ensure uniqueness
            while Article.objects.filter(submission_id=self.submission_id).exists():
                self.submission_id = generate_submission_id()
        
        # Set submitted_at when transitioning to SUBMITTED
        if self.status == ArticleStatus.SUBMITTED.value and not self.submitted_at:
            self.submitted_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def transition_status(self, new_status: ArticleStatus, user_role: str, user=None):
        """
        Transition article to new status with validation.
        
        Args:
            new_status: Target ArticleStatus
            user_role: User role (AUTHOR, REVIEWER, ADMIN)
            user: User object for audit logging
        
        Raises:
            ValidationError: If transition is not allowed
        """
        current_status = ArticleStatus(self.status)
        from_status_value = current_status.value
        
        # Handle auto-transitions before validation
        final_status = new_status
        
        # Auto-transition: SUBMITTED -> DESK_CHECK
        # Validate the user can transition to SUBMITTED first, then auto-transition to DESK_CHECK
        if new_status == ArticleStatus.SUBMITTED:
            # Validate user can transition to SUBMITTED
            if not can_transition(current_status, ArticleStatus.SUBMITTED, user_role):
                raise ValidationError(
                    f"Transition from {current_status.value} to {ArticleStatus.SUBMITTED.value} "
                    f"is not allowed for role {user_role}"
                )
            # Auto-transition to DESK_CHECK (SYSTEM transition)
            final_status = ArticleStatus.DESK_CHECK
        
        # Note: ACCEPTED no longer auto-transitions to payment states
        # Payment status is managed separately via payment_status field
        
        # Validate transition for non-auto-transitions
        else:
            if not can_transition(current_status, final_status, user_role):
                raise ValidationError(
                    f"Transition from {current_status.value} to {final_status.value} "
                    f"is not allowed for role {user_role}"
                )
        
        # Business rule: Payment gate check is handled in service layer
        # (not in transition_status to keep separation of concerns)
        
        # Business rule: Certificate only after publication
        if final_status == ArticleStatus.CERTIFICATE_ISSUED:
            if not can_issue_certificate(current_status):
                raise ValidationError(
                    "Certificate can only be issued after publication."
                )
        
        # Update status
        self.status = final_status.value
        self.save()
        
        # Log the transition
        from apps.audit.models import AuditLog
        AuditLog.objects.create(
            actor=user,
            action='STATUS_CHANGE',
            entity_type='ARTICLE',
            entity_id=self.id,
            metadata={
                'from_status': from_status_value,
                'to_status': self.status,
                'submission_id': self.submission_id,
                'requested_status': new_status.value if new_status != final_status else None
            }
        )
    
    def get_payment_status(self) -> str:
        """Get current payment status."""
        # Return the payment_status field value
        return self.payment_status
    
    def can_be_published_by(self, user) -> bool:
        """Check if article can be published by the given user."""
        if user.role != 'REVIEWER' and user.role != 'ADMIN':
            return False
        
        payment_status = self.get_payment_status()
        return can_publish(ArticleStatus(self.status), payment_status)
    
    @property
    def current_status_enum(self):
        """Get current status as ArticleStatus enum."""
        return ArticleStatus(self.status)


class ArticleVersion(models.Model):
    """
    Version history for article revisions.
    """
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='versions'
    )
    version_number = models.PositiveIntegerField()
    manuscript_file = models.FileField(
        upload_to='articles/manuscripts/',
        help_text='Manuscript file (PDF/DOCX)'
    )
    revision_type = models.CharField(
        max_length=20,
        choices=[
            ('INITIAL', 'Initial Submission'),
            ('MINOR', 'Minor Revision'),
            ('MAJOR', 'Major Revision'),
        ],
        default='INITIAL'
    )
    notes = models.TextField(blank=True, help_text='Author notes for this revision')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='article_versions'
    )
    
    class Meta:
        db_table = 'article_versions'
        ordering = ['-version_number']
        unique_together = ['article', 'version_number']
    
    def __str__(self):
        return f"{self.article.submission_id} v{self.version_number}"


class Review(models.Model):
    """
    Review model for reviewer comments and decisions.
    """
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    reviewer = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='reviews',
        limit_choices_to={'role': 'REVIEWER'}
    )
    
    # Review Content
    recommendation = models.CharField(
        max_length=20,
        choices=[
            ('ACCEPT', 'Accept'),
            ('REVISE', 'Revise'),
            ('REJECT', 'Reject'),
        ]
    )
    comments_to_author = models.TextField(
        help_text='Comments visible to the author'
    )
    confidential_comments = models.TextField(
        blank=True,
        help_text='Confidential comments (not visible to author)'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']
        unique_together = ['article', 'reviewer']
    
    def __str__(self):
        return f"Review by {self.reviewer.email} for {self.article.submission_id}"

