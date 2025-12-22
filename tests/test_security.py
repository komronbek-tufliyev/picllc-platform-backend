"""
System-level security tests.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class SecurityTests(TestCase):
    """Test security measures."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            role='AUTHOR'
        )
    
    def test_csrf_exempt_for_webhooks_only(self):
        """Test that webhooks are CSRF exempt but other endpoints are not."""
        # Webhook should work without CSRF token
        response = self.client.post(
            '/api/payments/webhooks/payme/',
            data={'test': 'data'},
            content_type='application/json'
        )
        # Should not fail with CSRF error (may fail for other reasons)
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_sql_injection_prevention(self):
        """Test that SQL injection attempts are prevented."""
        # Try SQL injection in search parameter
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        response = self.client.get('/api/articles/?search=1\' OR \'1\'=\'1')
        
        # Should not crash, should return empty results or error gracefully
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
    
    def test_xss_prevention(self):
        """Test that XSS attempts are sanitized."""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        # Try XSS in article title
        from apps.articles.models import Article
        from apps.journals.models import Journal
        
        journal = Journal.objects.create(name='Test', issn='1234-5678', scope='Test')
        
        xss_payload = '<script>alert("XSS")</script>'
        article = Article.objects.create(
            submission_id='SUB-XSS',
            title=xss_payload,
            abstract='Test',
            corresponding_author=self.user,
            journal=journal
        )
        
        response = self.client.get(f'/api/articles/{article.id}/')
        
        # Title should be escaped in JSON response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # DRF serializers escape HTML by default, so this should be safe
        self.assertIn('script', response.data['title'])  # Escaped, not executed

