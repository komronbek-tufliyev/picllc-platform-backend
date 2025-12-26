"""
Serializers for articles.
"""
from rest_framework import serializers
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from .models import Article, ArticleVersion, Review
from .workflow import ArticleStatus, get_allowed_transitions
from apps.journals.serializers import JournalListSerializer
from apps.accounts.serializers import UserSerializer


class ArticleVersionSerializer(serializers.ModelSerializer):
    """Serializer for ArticleVersion."""
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    
    class Meta:
        model = ArticleVersion
        fields = [
            'id', 'version_number', 'manuscript_file', 'revision_type',
            'notes', 'created_at', 'created_by', 'created_by_email'
        ]
        read_only_fields = ['id', 'version_number', 'created_at', 'created_by']


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Review."""
    reviewer_email = serializers.EmailField(source='reviewer.email', read_only=True)
    reviewer_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'reviewer', 'reviewer_email', 'reviewer_name',
            'recommendation', 'comments_to_author', 'confidential_comments',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'reviewer', 'created_at', 'updated_at']
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_reviewer_name(self, obj) -> str:
        """Get reviewer's full name or email."""
        if obj.reviewer:
            return f"{obj.reviewer.first_name} {obj.reviewer.last_name}".strip() or obj.reviewer.email
        return None


class ArticleListSerializer(serializers.ModelSerializer):
    """Simplified serializer for article lists."""
    journal = JournalListSerializer(read_only=True)
    corresponding_author_email = serializers.EmailField(source='corresponding_author.email', read_only=True)
    
    class Meta:
        model = Article
        fields = [
            'id', 'submission_id', 'title', 'journal', 'corresponding_author_email',
            'status', 'created_at', 'updated_at', 'submitted_at'
        ]


class ArticleDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for article with nested data."""
    journal = JournalListSerializer(read_only=True)
    corresponding_author = UserSerializer(read_only=True)
    versions = ArticleVersionSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    allowed_transitions = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()
    has_certificate = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = [
            'id', 'submission_id', 'title', 'abstract', 'keywords',
            'corresponding_author', 'authors', 'journal',
            'status', 'ethics_declaration', 'originality_declaration',
            'publication_url', 'publication_date',
            'created_at', 'updated_at', 'submitted_at',
            'versions', 'reviews', 'allowed_transitions',
            'payment_status', 'has_certificate'
        ]
        read_only_fields = [
            'id', 'submission_id', 'created_at', 'updated_at',
            'submitted_at', 'allowed_transitions', 'payment_status', 'has_certificate'
        ]
    
    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_allowed_transitions(self, obj) -> list:
        """Get allowed status transitions for current user."""
        request = self.context.get('request')
        if request and request.user:
            user_role = request.user.role
            current_status = ArticleStatus(obj.status)
            transitions = get_allowed_transitions(current_status, user_role)
            return [status.value for status in transitions]
        return []
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_payment_status(self, obj):
        """
        Get payment status.
        
        Payment status is separate from article status and tracks the payment lifecycle:
        - NONE: No invoice yet (article not accepted)
        - PENDING: Invoice created, payment not completed
        - PAID: Payment completed
        - NOT_REQUIRED: APC not required for this article
        """
        return obj.get_payment_status()
    
    @extend_schema_field(OpenApiTypes.BOOL)
    def get_has_certificate(self, obj) -> bool:
        """Check if article has a certificate."""
        try:
            return obj.certificate is not None
        except Exception:
            return False


class ArticleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating articles."""
    
    class Meta:
        model = Article
        fields = [
            'title', 'abstract', 'keywords', 'authors', 'journal',
            'ethics_declaration', 'originality_declaration'
        ]
    
    def create(self, validated_data):
        """Create article with DRAFT status."""
        validated_data['corresponding_author'] = self.context['request'].user
        validated_data['status'] = ArticleStatus.DRAFT.value
        return super().create(validated_data)


class ArticleUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating article metadata (DRAFT only)."""
    
    class Meta:
        model = Article
        fields = [
            'title', 'abstract', 'keywords', 'authors',
            'ethics_declaration', 'originality_declaration'
        ]
    
    def validate(self, attrs):
        """Ensure article is in DRAFT status."""
        instance = self.instance
        if instance.status != ArticleStatus.DRAFT.value:
            raise ValidationError("Article can only be edited in DRAFT status.")
        return attrs


class ArticleWorkflowActionSerializer(serializers.Serializer):
    """
    Serializer for workflow actions.
    
    Note: Payment operations (initiate_payment, mark_as_paid) do NOT change Article.status.
    Payment is tracked separately via Article.payment_status field.
    """
    action = serializers.ChoiceField(choices=[
        ('submit', 'Submit article'),
        ('desk_reject', 'Desk reject'),
        ('send_to_review', 'Send to review'),
        ('request_revision', 'Request revision'),
        ('accept', 'Accept article'),
        ('reject', 'Reject article'),
        ('move_to_production', 'Move to production - requires payment_status = PAID or NOT_REQUIRED'),
        ('publish', 'Publish article - requires payment_status = PAID or NOT_REQUIRED'),
    ])
    revision_type = serializers.ChoiceField(
        choices=[('MINOR', 'Minor'), ('MAJOR', 'Major')],
        required=False,
        help_text='Required for request_revision action'
    )
    publication_url = serializers.URLField(
        required=False,
        help_text='Required for publish action'
    )
    comments = serializers.CharField(
        required=False,
        help_text='Comments for revision request or rejection'
    )

