"""
Service layer for article workflow actions.
All state transitions must go through this service layer for validation.
"""
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import models
from .models import Article, ArticleVersion, Review
from .workflow import ArticleStatus
from apps.audit.models import AuditLog
from apps.payments.models import Invoice


class ArticleWorkflowService:
    """Service for handling article workflow transitions."""
    
    @staticmethod
    def submit_article(article: Article, user) -> Article:
        """Submit article (DRAFT -> SUBMITTED)."""
        if article.status != ArticleStatus.DRAFT.value:
            raise ValidationError("Article must be in DRAFT status to submit.")
        
        if article.corresponding_author != user:
            raise ValidationError("Only the corresponding author can submit the article.")
        
        # Check required fields
        if not article.title or not article.abstract:
            raise ValidationError("Title and abstract are required.")
        
        if not article.ethics_declaration or not article.originality_declaration:
            raise ValidationError("Ethics and originality declarations are required.")
        
        # Check if article has at least one version
        if not article.versions.exists():
            raise ValidationError("Article must have at least one manuscript file.")
        
        article.transition_status(ArticleStatus.SUBMITTED, user.role, user)
        
        # Log submission
        AuditLog.objects.create(
            actor=user,
            action='ARTICLE_SUBMITTED',
            entity_type='ARTICLE',
            entity_id=article.id,
            metadata={'submission_id': article.submission_id}
        )
        
        # Send email notification
        from apps.notifications.tasks import send_article_submitted_email
        send_article_submitted_email.delay(article.id)
        
        return article
    
    @staticmethod
    def desk_reject(article: Article, user, comments: str = '') -> Article:
        """Desk reject article."""
        current_status = ArticleStatus(article.status)
        
        if current_status not in [ArticleStatus.DESK_CHECK, ArticleStatus.SUBMITTED]:
            raise ValidationError("Article must be in DESK_CHECK or SUBMITTED status.")
        
        article.transition_status(ArticleStatus.REJECTED, user.role, user)
        
        # Create review record
        review = Review.objects.create(
            article=article,
            reviewer=user,
            recommendation='REJECT',
            comments_to_author=comments or 'Desk rejected',
            confidential_comments=''
        )
        
        # Send email notification
        from apps.notifications.tasks import send_article_rejected_email
        send_article_rejected_email.delay(article.id, review.comments_to_author)
        
        return article
    
    @staticmethod
    def send_to_review(article: Article, user) -> Article:
        """Send article to review (DESK_CHECK -> UNDER_REVIEW)."""
        current_status = ArticleStatus(article.status)
        
        if current_status != ArticleStatus.DESK_CHECK:
            raise ValidationError("Article must be in DESK_CHECK status.")
        
        article.transition_status(ArticleStatus.UNDER_REVIEW, user.role, user)
        
        return article
    
    @staticmethod
    def request_revision(
        article: Article,
        user,
        revision_type: str,
        comments: str
    ) -> Article:
        """Request revision (UNDER_REVIEW -> REVISION_REQUIRED)."""
        current_status = ArticleStatus(article.status)
        
        if current_status != ArticleStatus.UNDER_REVIEW:
            raise ValidationError("Article must be in UNDER_REVIEW status.")
        
        if revision_type not in ['MINOR', 'MAJOR']:
            raise ValidationError("Revision type must be MINOR or MAJOR.")
        
        article.transition_status(ArticleStatus.REVISION_REQUIRED, user.role, user)
        
        # Create review record
        review = Review.objects.create(
            article=article,
            reviewer=user,
            recommendation='REVISE',
            comments_to_author=comments,
            confidential_comments=f'Revision type: {revision_type}'
        )
        
        # Send email notification
        from apps.notifications.tasks import send_revision_requested_email
        send_revision_requested_email.delay(article.id, review.comments_to_author)
        
        return article
    
    @staticmethod
    def submit_revision(
        article: Article,
        user,
        manuscript_file,
        notes: str = ''
    ) -> ArticleVersion:
        """Submit revised version."""
        current_status = ArticleStatus(article.status)
        
        if current_status != ArticleStatus.REVISION_REQUIRED:
            raise ValidationError("Article must be in REVISION_REQUIRED status.")
        
        if article.corresponding_author != user:
            raise ValidationError("Only the corresponding author can submit revisions.")
        
        # Get next version number
        max_version = article.versions.aggregate(
            max_version=models.Max('version_number')
        )['max_version'] or 0
        
        version = ArticleVersion.objects.create(
            article=article,
            version_number=max_version + 1,
            manuscript_file=manuscript_file,
            revision_type='MINOR',  # Could be determined from review
            notes=notes,
            created_by=user
        )
        
        # Transition to REVISED_SUBMITTED
        article.transition_status(ArticleStatus.REVISED_SUBMITTED, user.role, user)
        
        return version
    
    @staticmethod
    def accept_article(article: Article, user, comments: str = '') -> Article:
        """Accept article (UNDER_REVIEW -> ACCEPTED)."""
        current_status = ArticleStatus(article.status)
        
        if current_status not in [ArticleStatus.UNDER_REVIEW, ArticleStatus.REVISED_SUBMITTED]:
            raise ValidationError("Article must be in UNDER_REVIEW or REVISED_SUBMITTED status.")
        
        article.transition_status(ArticleStatus.ACCEPTED, user.role, user)
        
        # Create review record
        review = Review.objects.create(
            article=article,
            reviewer=user,
            recommendation='ACCEPT',
            comments_to_author=comments or 'Article accepted',
            confidential_comments=''
        )
        
        # Create invoice if journal requires APC
        if article.journal.apc_enabled and article.journal.apc_amount > 0:
            Invoice.objects.get_or_create(
                article=article,
                defaults={
                    'amount': article.journal.apc_amount,
                    'currency': article.journal.currency,
                    'status': Invoice.Status.PENDING
                }
            )
        
        # Send email notification
        from apps.notifications.tasks import send_article_accepted_email
        send_article_accepted_email.delay(article.id)
        
        return article
    
    @staticmethod
    def reject_article(article: Article, user, comments: str = '') -> Article:
        """Reject article (UNDER_REVIEW -> REJECTED)."""
        current_status = ArticleStatus(article.status)
        
        if current_status not in [ArticleStatus.UNDER_REVIEW, ArticleStatus.REVISED_SUBMITTED]:
            raise ValidationError("Article must be in UNDER_REVIEW or REVISED_SUBMITTED status.")
        
        article.transition_status(ArticleStatus.REJECTED, user.role, user)
        
        # Create review record
        review = Review.objects.create(
            article=article,
            reviewer=user,
            recommendation='REJECT',
            comments_to_author=comments or 'Article rejected',
            confidential_comments=''
        )
        
        # Send email notification
        from apps.notifications.tasks import send_article_rejected_email
        send_article_rejected_email.delay(article.id, review.comments_to_author)
        
        return article
    
    @staticmethod
    def publish_article(
        article: Article,
        user,
        publication_url: str
    ) -> Article:
        """Publish article (PAID/PRODUCTION -> PUBLISHED)."""
        current_status = ArticleStatus(article.status)
        
        # Business rule: Payment must be PAID
        payment_status = article.get_payment_status()
        if payment_status != 'PAID':
            raise ValidationError(
                "Article cannot be published. Payment must be PAID."
            )
        
        if current_status not in [ArticleStatus.PAID, ArticleStatus.PRODUCTION]:
            raise ValidationError("Article must be in PAID or PRODUCTION status.")
        
        article.publication_url = publication_url
        article.publication_date = timezone.now().date()
        article.transition_status(ArticleStatus.PUBLISHED, user.role, user)
        
        # Log publication
        AuditLog.objects.create(
            actor=user,
            action='ARTICLE_PUBLISHED',
            entity_type='ARTICLE',
            entity_id=article.id,
            metadata={
                'submission_id': article.submission_id,
                'publication_url': publication_url
            }
        )
        
        # Send email notification
        from apps.notifications.tasks import send_article_published_email
        send_article_published_email.delay(article.id)
        
        return article

