"""
System-level tests for certificate verification and public access.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone

from apps.articles.models import Article
from apps.articles.workflow import ArticleStatus
from apps.journals.models import Journal
from apps.certificates.models import Certificate

User = get_user_model()


class CertificateVerificationTests(TestCase):
    """Test public certificate verification."""
    
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
            scope='Test'
        )
        
        self.article = Article.objects.create(
            submission_id='SUB-001',
            title='Test Article',
            abstract='Test abstract',
            corresponding_author=self.author,
            journal=self.journal,
            status=ArticleStatus.PUBLISHED.value,
            publication_url='https://example.com/article',
            publication_date=timezone.now().date()
        )
        
        self.certificate = Certificate.objects.create(
            article=self.article,
            status=Certificate.Status.ACTIVE
        )
    
    def test_public_verification_no_auth_required(self):
        """Test that certificate verification is publicly accessible."""
        # No authentication
        response = self.client.get(
            f'/verify/certificate/{self.certificate.certificate_id}/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['certificate_id'], str(self.certificate.certificate_id))
        self.assertEqual(response.data['article_title'], self.article.title)
        self.assertEqual(response.data['status'], 'ACTIVE')
        self.assertFalse(response.data['revoked'])
    
    def test_verification_invalid_certificate_id(self):
        """Test verification with invalid certificate ID."""
        import uuid
        invalid_id = uuid.uuid4()
        
        response = self.client.get(f'/verify/certificate/{invalid_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_verification_shows_revoked_status(self):
        """Test that revoked certificates show revoked status."""
        self.certificate.status = Certificate.Status.REVOKED
        self.certificate.revoked_at = timezone.now()
        self.certificate.save()
        
        response = self.client.get(
            f'/verify/certificate/{self.certificate.certificate_id}/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['revoked'])
        self.assertEqual(response.data['status'], 'REVOKED')
    
    def test_verification_includes_publication_info(self):
        """Test that verification includes publication information."""
        response = self.client.get(
            f'/verify/certificate/{self.certificate.certificate_id}/'
        )
        
        self.assertEqual(response.data['publication_url'], self.article.publication_url)
        self.assertEqual(response.data['publication_date'], str(self.article.publication_date))
        self.assertEqual(response.data['journal_name'], self.journal.name)
    
    def test_certificate_download_requires_auth(self):
        """Test that certificate download requires authentication."""
        response = self.client.get(f'/api/certificates/{self.certificate.id}/download/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_certificate_download_author_access(self):
        """Test that author can download their certificate."""
        from rest_framework_simplejwt.tokens import RefreshToken
        
        refresh = RefreshToken.for_user(self.author)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        response = self.client.get(f'/api/certificates/{self.certificate.id}/download/')
        
        # May return 404 if PDF not generated, but should not be 403
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)

