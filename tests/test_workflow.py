"""
System-level tests for workflow state machine and bypass prevention.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.exceptions import ValidationError

from apps.articles.models import Article
from apps.articles.workflow import ArticleStatus
from apps.journals.models import Journal

User = get_user_model()


class WorkflowBypassPreventionTests(TestCase):
    """Test that workflow bypasses are prevented."""
    
    def setUp(self):
        self.client = APIClient()
        
        self.author = User.objects.create_user(
            email='author@example.com',
            username='author',
            password='pass123',
            role='AUTHOR'
        )
        
        self.reviewer = User.objects.create_user(
            email='reviewer@example.com',
            username='reviewer',
            password='pass123',
            role='REVIEWER'
        )
        
        self.journal = Journal.objects.create(
            name='Test Journal',
            issn='1234-5678',
            scope='Test',
            apc_enabled=True,
            apc_amount=500.00
        )
        
        self.article = Article.objects.create(
            submission_id='SUB-001',
            title='Test Article',
            abstract='Test abstract',
            corresponding_author=self.author,
            journal=self.journal,
            status=ArticleStatus.DRAFT.value
        )
    
    def test_author_cannot_bypass_submission(self):
        """Test that author cannot directly set status to UNDER_REVIEW."""
        refresh = RefreshToken.for_user(self.author)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        # Try to directly transition to UNDER_REVIEW (should fail)
        response = self.client.post(f'/api/articles/{self.article.id}/workflow_action/', {
            'action': 'send_to_review'
        })
        
        # Should fail because article is in DRAFT, not DESK_CHECK
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_invalid_transition_rejected(self):
        """Test that invalid state transitions are rejected."""
        # Set article to DRAFT
        self.article.status = ArticleStatus.DRAFT.value
        self.article.save()
        
        # Try to transition directly to ACCEPTED (invalid)
        from apps.articles.services import ArticleWorkflowService
        
        with self.assertRaises(ValidationError):
            ArticleWorkflowService.accept_article(self.article, self.reviewer, '')
    
    def test_payment_before_publication_enforced(self):
        """Test that payment is required before publication."""
        # Set article to PAID status without payment
        self.article.status = ArticleStatus.PAID.value
        self.article.save()
        
        # But invoice doesn't exist or is not PAID
        refresh = RefreshToken.for_user(self.reviewer)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        response = self.client.post(f'/api/articles/{self.article.id}/workflow_action/', {
            'action': 'publish',
            'publication_url': 'https://example.com/article'
        })
        
        # Should fail because payment status check fails
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_certificate_only_after_publication(self):
        """Test that certificate can only be issued after publication."""
        from apps.certificates.models import Certificate
        
        # Try to create certificate for non-published article
        self.article.status = ArticleStatus.ACCEPTED.value
        self.article.save()
        
        certificate = Certificate(article=self.article)
        
        with self.assertRaises(ValidationError):
            certificate.clean()
            certificate.save()
    
    def test_workflow_service_enforces_rules(self):
        """Test that workflow service enforces all business rules."""
        from apps.articles.services import ArticleWorkflowService
        
        # Submit article
        ArticleWorkflowService.submit_article(self.article, self.author)
        self.article.refresh_from_db()
        self.assertEqual(self.article.status, ArticleStatus.DESK_CHECK.value)
        
        # Send to review
        ArticleWorkflowService.send_to_review(self.article, self.reviewer)
        self.article.refresh_from_db()
        self.assertEqual(self.article.status, ArticleStatus.UNDER_REVIEW.value)
        
        # Accept article
        ArticleWorkflowService.accept_article(self.article, self.reviewer, 'Accepted')
        self.article.refresh_from_db()
        # Should transition to PAYMENT_PENDING (APC enabled)
        self.assertEqual(self.article.status, ArticleStatus.PAYMENT_PENDING.value)
    
    def test_only_corresponding_author_can_submit(self):
        """Test that only corresponding author can submit article."""
        other_author = User.objects.create_user(
            email='other@example.com',
            username='other',
            password='pass123',
            role='AUTHOR'
        )
        
        from apps.articles.services import ArticleWorkflowService
        
        with self.assertRaises(ValidationError):
            ArticleWorkflowService.submit_article(self.article, other_author)
    
    def test_only_reviewer_can_publish(self):
        """Test that only reviewers can publish articles."""
        refresh = RefreshToken.for_user(self.author)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        # Set article to PAID
        self.article.status = ArticleStatus.PAID.value
        self.article.save()
        
        # Author tries to publish
        response = self.client.post(f'/api/articles/{self.article.id}/workflow_action/', {
            'action': 'publish',
            'publication_url': 'https://example.com/article'
        })
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

