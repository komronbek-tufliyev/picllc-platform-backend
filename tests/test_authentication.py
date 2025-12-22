"""
System-level tests for authentication and JWT tokens.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
from django.utils import timezone
import json

User = get_user_model()


class JWTAuthenticationTests(TestCase):
    """Test JWT authentication, token expiry, and refresh."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            role='AUTHOR'
        )
    
    def test_jwt_login_success(self):
        """Test successful JWT login."""
        response = self.client.post('/api/auth/login/', {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'test@example.com')
    
    def test_jwt_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = self.client.post('/api/auth/login/', {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_jwt_token_contains_role(self):
        """Test that JWT token contains user role."""
        response = self.client.post('/api/auth/login/', {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        
        access_token = response.data['access']
        
        # Decode token to verify role
        from rest_framework_simplejwt.tokens import UntypedToken
        from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
        from jwt import decode as jwt_decode
        from django.conf import settings
        
        try:
            decoded = jwt_decode(access_token, settings.SECRET_KEY, algorithms=["HS256"])
            self.assertEqual(decoded['role'], 'AUTHOR')
            self.assertEqual(decoded['email'], 'test@example.com')
        except Exception as e:
            self.fail(f"Token decoding failed: {e}")
    
    def test_access_token_required(self):
        """Test that protected endpoints require access token."""
        response = self.client.get('/api/articles/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_access_token_valid(self):
        """Test access with valid token."""
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get('/api/auth/profile/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_token_refresh(self):
        """Test token refresh endpoint."""
        refresh = RefreshToken.for_user(self.user)
        refresh_token = str(refresh)
        
        response = self.client.post('/api/auth/token/refresh/', {
            'refresh': refresh_token
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_token_refresh_invalid(self):
        """Test refresh with invalid token."""
        response = self.client.post('/api/auth/token/refresh/', {
            'refresh': 'invalid_token'
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_expired_token_rejected(self):
        """Test that expired tokens are rejected."""
        # Create token with very short expiry
        from rest_framework_simplejwt.tokens import AccessToken
        from django.conf import settings
        
        token = AccessToken.for_user(self.user)
        token.set_exp(from_time=timezone.now() - timedelta(hours=1))
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token)}')
        response = self.client.get('/api/auth/profile/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RoleEnforcementTests(TestCase):
    """Test role-based access control enforcement."""
    
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
        
        self.admin = User.objects.create_user(
            email='admin@example.com',
            username='admin',
            password='pass123',
            role='ADMIN'
        )
    
    def test_author_cannot_access_admin_endpoints(self):
        """Test that authors cannot access admin-only endpoints."""
        refresh = RefreshToken.for_user(self.author)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        # Try to access audit logs (admin only)
        response = self.client.get('/api/audit/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_reviewer_cannot_access_admin_endpoints(self):
        """Test that reviewers cannot access admin-only endpoints."""
        refresh = RefreshToken.for_user(self.reviewer)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        # Try to create journal (admin only)
        response = self.client.post('/api/journals/', {
            'name': 'Test Journal',
            'issn': '1234-5678',
            'scope': 'Test scope'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_admin_can_access_all_endpoints(self):
        """Test that admin can access all endpoints."""
        refresh = RefreshToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        # Access audit logs
        response = self.client.get('/api/audit/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Access journals
        response = self.client.get('/api/journals/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_author_sees_only_own_articles(self):
        """Test that authors only see their own articles."""
        from apps.articles.models import Article
        from apps.journals.models import Journal
        
        journal = Journal.objects.create(
            name='Test Journal',
            issn='1234-5678',
            scope='Test'
        )
        
        # Create article by author
        article1 = Article.objects.create(
            submission_id='SUB-001',
            title='Author Article',
            abstract='Test',
            corresponding_author=self.author,
            journal=journal
        )
        
        # Create article by another author
        other_author = User.objects.create_user(
            email='other@example.com',
            username='other',
            password='pass123',
            role='AUTHOR'
        )
        article2 = Article.objects.create(
            submission_id='SUB-002',
            title='Other Article',
            abstract='Test',
            corresponding_author=other_author,
            journal=journal
        )
        
        refresh = RefreshToken.for_user(self.author)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        response = self.client.get('/api/articles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only see own article
        article_ids = [item['id'] for item in response.data['results']]
        self.assertIn(article1.id, article_ids)
        self.assertNotIn(article2.id, article_ids)

