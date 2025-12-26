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
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

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
    
    @extend_schema(
        summary="Perform workflow action on article",
        description="""
        Execute workflow transitions for articles. 
        
        **Important Notes:**
        - `Article.status` represents ONLY the scientific/editorial lifecycle
        - Payment is tracked separately via `Article.payment_status` field
        - Payment operations (initiate_payment, mark_as_paid) do NOT change `Article.status`
        
        **Payment Gates:**
        - `move_to_production`: Requires `payment_status` = `PAID` or `NOT_REQUIRED`
        - `publish`: Requires `payment_status` = `PAID` or `NOT_REQUIRED`
        
        **Actions:**
        - `submit`: DRAFT → SUBMITTED → DESK_CHECK (auto)
        - `desk_reject`: DESK_CHECK/SUBMITTED → REJECTED (Admin only)
        - `send_to_review`: DESK_CHECK → UNDER_REVIEW (Admin only)
        - `request_revision`: UNDER_REVIEW → REVISION_REQUIRED (Reviewer/Admin)
        - `accept`: UNDER_REVIEW → ACCEPTED, creates invoice if APC required (Admin only)
        - `reject`: UNDER_REVIEW → REJECTED (Admin only)
        - `move_to_production`: ACCEPTED → PRODUCTION (Admin only, payment gate)
        - `publish`: ACCEPTED/PRODUCTION → PUBLISHED (Admin only, payment gate)
        """,
        request=ArticleWorkflowActionSerializer,
        responses={
            200: ArticleDetailSerializer,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "Accept article",
                value={"action": "accept", "comments": "Article accepted for publication"},
                request_only=True,
            ),
            OpenApiExample(
                "Move to production (payment gate)",
                value={"action": "move_to_production"},
                request_only=True,
                description="Requires payment_status = PAID or NOT_REQUIRED",
            ),
            OpenApiExample(
                "Publish article",
                value={
                    "action": "publish",
                    "publication_url": "https://journal.example.com/article/123"
                },
                request_only=True,
                description="Requires payment_status = PAID or NOT_REQUIRED",
            ),
            OpenApiExample(
                "Payment gate error",
                value={
                    "error": "Article cannot move to production. Payment status must be PAID or NOT_REQUIRED, but is currently PENDING."
                },
                response_only=True,
                status_codes=["400"],
            ),
        ],
    )
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
                if request.user.role != 'ADMIN':
                    return Response(
                        {'error': 'Only admins can desk reject articles.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                comments = serializer.validated_data.get('comments', '')
                service.desk_reject(article, request.user, comments)
                
            elif action_type == 'send_to_review':
                # Only ADMIN can send from DESK_CHECK; service validates status
                if request.user.role != 'ADMIN':
                    return Response(
                        {'error': 'Only admins can send articles to review from desk check.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                service.send_to_review(article, request.user)
                
            elif action_type == 'request_revision':
                if request.user.role not in ['REVIEWER', 'ADMIN']:
                    return Response(
                        {'error': 'Only reviewers or admins can request revisions.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                revision_type = serializer.validated_data.get('revision_type', 'MINOR')
                comments = serializer.validated_data.get('comments', '')
                service.request_revision(article, request.user, revision_type, comments)
                
            elif action_type == 'accept':
                if request.user.role != 'ADMIN':
                    return Response(
                        {'error': 'Only admins can accept articles.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                comments = serializer.validated_data.get('comments', '')
                service.accept_article(article, request.user, comments)
                
            elif action_type == 'reject':
                if request.user.role != 'ADMIN':
                    return Response(
                        {'error': 'Only admins can reject articles.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                comments = serializer.validated_data.get('comments', '')
                service.reject_article(article, request.user, comments)
                
            elif action_type == 'move_to_production':
                if request.user.role != 'ADMIN':
                    return Response(
                        {'error': 'Only admins can move articles to production.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                service.move_to_production(article, request.user)
                
            elif action_type == 'publish':
                if request.user.role != 'ADMIN':
                    return Response(
                        {'error': 'Only admins can publish articles.'},
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
    def upload_manuscript(self, request, pk=None):
        """Upload initial manuscript file (DRAFT status) or revised manuscript (REVISION_REQUIRED status)."""
        article = self.get_object()
        
        if article.corresponding_author != request.user:
            return Response(
                {'error': 'Only the corresponding author can upload manuscripts.'},
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
            
            # Handle initial upload (DRAFT status)
            if article.status == 'DRAFT':
                version = service.upload_initial_manuscript(article, request.user, manuscript_file, notes)
            # Handle revision upload (REVISION_REQUIRED status)
            elif article.status == 'REVISION_REQUIRED':
                version = service.submit_revision(article, request.user, manuscript_file, notes)
            else:
                return Response(
                    {'error': 'Article must be in DRAFT or REVISION_REQUIRED status to upload manuscript.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response(
                ArticleVersionSerializer(version).data,
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def upload_revision(self, request, pk=None):
        """Upload revised manuscript (REVISION_REQUIRED status only)."""
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

