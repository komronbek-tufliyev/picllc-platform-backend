"""
API views for articles.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError

from .models import Article, ArticleVersion, Review
from .serializers import (
    ArticleListSerializer,
    ArticleDetailSerializer,
    ArticleCreateSerializer,
    ArticleUpdateSerializer,
    ArticleWorkflowActionSerializer,
    ArticleVersionSerializer,
    ReviewSerializer
)
from .services import ArticleWorkflowService
from .throttling import ArticleSubmissionThrottle, ArticleWorkflowThrottle
from apps.accounts.permissions import (
    IsAuthor,
    IsReviewer,
    IsAdmin,
    IsAuthorOrAdmin,
    IsReviewerOrAdmin
)
from apps.journals.models import ReviewerJournalAssignment


class ArticleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for articles.
    
    - Authors: Can create, list own articles, update drafts, submit
    - Reviewers: Can list assigned articles, view details, perform actions
    - Admins: Full access
    """
    queryset = Article.objects.select_related(
        'corresponding_author', 'journal'
    ).prefetch_related('versions', 'reviews').all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'journal']
    search_fields = ['title', 'submission_id', 'abstract']
    ordering_fields = ['created_at', 'updated_at', 'submitted_at']
    ordering = ['-created_at']
    throttle_classes = [UserRateThrottle]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ArticleListSerializer
        elif self.action == 'create':
            return ArticleCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return ArticleUpdateSerializer
        return ArticleDetailSerializer
    
    def get_queryset(self):
        """Filter queryset based on user role."""
        user = self.request.user
        
        if user.role == 'AUTHOR':
            # Authors see only their own articles
            return self.queryset.filter(corresponding_author=user)
        elif user.role == 'REVIEWER':
            # Reviewers see articles from their assigned journals
            assigned_journals = ReviewerJournalAssignment.objects.filter(
                reviewer=user
            ).values_list('journal_id', flat=True)
            return self.queryset.filter(journal_id__in=assigned_journals)
        elif user.role == 'ADMIN':
            # Admins see all articles
            return self.queryset
        
        return Article.objects.none()
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action == 'create':
            return [IsAuthenticated()]  # Any authenticated user can create
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthorOrAdmin()]
        return super().get_permissions()
    
    def get_throttles(self):
        """Apply different throttles based on action."""
        if self.action == 'create':
            return [ArticleSubmissionThrottle()]
        elif self.action == 'workflow_action':
            return [ArticleWorkflowThrottle()]
        return super().get_throttles()
    
    def perform_create(self, serializer):
        """Create article with current user as corresponding author."""
        serializer.save(corresponding_author=self.request.user)
    
    @action(detail=True, methods=['post'], serializer_class=ArticleWorkflowActionSerializer)
    def workflow_action(self, request, pk=None):
        """Handle workflow actions."""
        article = self.get_object()
        serializer = ArticleWorkflowActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action_type = serializer.validated_data['action']
        service = ArticleWorkflowService()
        
        try:
            if action_type == 'submit':
                if request.user.role != 'AUTHOR':
                    return Response(
                        {'error': 'Only authors can submit articles.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                service.submit_article(article, request.user)
                
            elif action_type == 'desk_reject':
                if request.user.role not in ['REVIEWER', 'ADMIN']:
                    return Response(
                        {'error': 'Only reviewers can desk reject articles.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                comments = serializer.validated_data.get('comments', '')
                service.desk_reject(article, request.user, comments)
                
            elif action_type == 'send_to_review':
                if request.user.role not in ['REVIEWER', 'ADMIN']:
                    return Response(
                        {'error': 'Only reviewers can send articles to review.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                service.send_to_review(article, request.user)
                
            elif action_type == 'request_revision':
                if request.user.role not in ['REVIEWER', 'ADMIN']:
                    return Response(
                        {'error': 'Only reviewers can request revisions.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                revision_type = serializer.validated_data.get('revision_type', 'MINOR')
                comments = serializer.validated_data.get('comments', '')
                service.request_revision(article, request.user, revision_type, comments)
                
            elif action_type == 'accept':
                if request.user.role not in ['REVIEWER', 'ADMIN']:
                    return Response(
                        {'error': 'Only reviewers can accept articles.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                comments = serializer.validated_data.get('comments', '')
                service.accept_article(article, request.user, comments)
                
            elif action_type == 'reject':
                if request.user.role not in ['REVIEWER', 'ADMIN']:
                    return Response(
                        {'error': 'Only reviewers can reject articles.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                comments = serializer.validated_data.get('comments', '')
                service.reject_article(article, request.user, comments)
                
            elif action_type == 'publish':
                if request.user.role not in ['REVIEWER', 'ADMIN']:
                    return Response(
                        {'error': 'Only reviewers can publish articles.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                publication_url = serializer.validated_data.get('publication_url')
                if not publication_url:
                    return Response(
                        {'error': 'Publication URL is required.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                service.publish_article(article, request.user, publication_url)
            
            article.refresh_from_db()
            return Response(
                ArticleDetailSerializer(article, context={'request': request}).data,
                status=status.HTTP_200_OK
            )
            
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def upload_revision(self, request, pk=None):
        """Upload revised manuscript."""
        article = self.get_object()
        
        if article.status != 'REVISION_REQUIRED':
            return Response(
                {'error': 'Article must be in REVISION_REQUIRED status.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if article.corresponding_author != request.user:
            return Response(
                {'error': 'Only the corresponding author can upload revisions.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        manuscript_file = request.FILES.get('manuscript_file')
        if not manuscript_file:
            return Response(
                {'error': 'Manuscript file is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        notes = request.data.get('notes', '')
        
        try:
            service = ArticleWorkflowService()
            version = service.submit_revision(article, request.user, manuscript_file, notes)
            return Response(
                ArticleVersionSerializer(version).data,
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """Get article timeline/audit log."""
        article = self.get_object()
        
        from apps.audit.models import AuditLog
        logs = AuditLog.objects.filter(
            entity_type='ARTICLE',
            entity_id=article.id
        ).order_by('created_at')
        
        from apps.audit.serializers import AuditLogSerializer
        return Response(
            AuditLogSerializer(logs, many=True).data
        )

