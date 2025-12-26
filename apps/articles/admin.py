from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import Article, ArticleVersion, Review
from .services import ArticleWorkflowService
from .workflow import ArticleStatus, get_allowed_transitions


class ArticleVersionInline(admin.TabularInline):
    """Inline admin for article versions."""
    model = ArticleVersion
    extra = 0
    readonly_fields = ('version_number', 'created_at', 'created_by')
    fields = ('version_number', 'manuscript_file', 'revision_type', 'notes', 'created_at', 'created_by')


class ReviewInline(admin.TabularInline):
    """Inline admin for reviews."""
    model = Review
    extra = 0
    readonly_fields = ('reviewer', 'created_at', 'updated_at')
    fields = ('reviewer', 'recommendation', 'comments_to_author', 'created_at')


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('submission_id', 'title', 'journal', 'corresponding_author', 'status', 'payment_status', 'allowed_transitions_display', 'created_at')
    list_filter = ('status', 'payment_status', 'journal', 'created_at')
    search_fields = ('submission_id', 'title', 'corresponding_author__email')
    readonly_fields = ('submission_id', 'status', 'payment_status', 'allowed_transitions_display', 'created_at', 'updated_at', 'submitted_at')
    inlines = [ArticleVersionInline, ReviewInline]
    actions = [
        'admin_send_to_review',
        'admin_request_revision',
        'admin_accept_article',
        'admin_reject_article',
        'admin_desk_reject',
        'admin_move_to_production',
        'admin_publish_article',
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('submission_id', 'title', 'abstract', 'keywords', 'journal')
        }),
        ('Authors', {
            'fields': ('corresponding_author', 'authors')
        }),
        ('Scientific Workflow', {
            'fields': ('status', 'submitted_at', 'allowed_transitions_display'),
            'description': 'Article.status tracks the scientific/editorial lifecycle only. Payment never modifies this field. Use workflow actions below to transition states.'
        }),
        ('Payment Status', {
            'fields': ('payment_status',),
            'description': 'Payment status is separate from scientific workflow. Values: NONE, PENDING, PAID, NOT_REQUIRED. Payment operations update this field, not Article.status. Payment gates: move_to_production and publish require PAID or NOT_REQUIRED.'
        }),
        ('Declarations', {
            'fields': ('ethics_declaration', 'originality_declaration')
        }),
        ('Publication', {
            'fields': ('publication_url', 'publication_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related."""
        qs = super().get_queryset(request)
        return qs.select_related('journal', 'corresponding_author').prefetch_related('versions', 'reviews')
    
    def allowed_transitions_display(self, obj):
        """Display allowed workflow transitions for current status and admin role."""
        if not obj:
            return '-'
        current_status = ArticleStatus(obj.status)
        allowed = get_allowed_transitions(current_status, 'ADMIN')
        if not allowed:
            return 'No transitions available (terminal state or requires different role)'
        return ', '.join([s.value for s in allowed])
    allowed_transitions_display.short_description = 'Allowed Transitions (Admin)'
    
    def get_actions(self, request):
        """Restrict workflow actions to superadmins only."""
        actions = super().get_actions(request)
        if not request.user.is_superuser:
            # Remove workflow actions for non-superusers
            workflow_actions = [
                'admin_send_to_review',
                'admin_request_revision',
                'admin_accept_article',
                'admin_reject_article',
                'admin_desk_reject',
                'admin_move_to_production',
                'admin_publish_article',
            ]
            for action_name in workflow_actions:
                actions.pop(action_name, None)
        return actions
    
    # Workflow Actions (superadmin only)
    def admin_send_to_review(self, request, queryset):
        """Send articles to review (DESK_CHECK → UNDER_REVIEW)."""
        if not request.user.is_superuser:
            self.message_user(request, "Only superadmins can perform workflow actions.", level=messages.ERROR)
            return
        
        service = ArticleWorkflowService()
        success_count = 0
        error_count = 0
        
        for article in queryset:
            try:
                service.send_to_review(article, request.user)
                success_count += 1
            except ValidationError as e:
                self.message_user(request, f"Article {article.submission_id}: {str(e)}", level=messages.ERROR)
                error_count += 1
        
        if success_count > 0:
            self.message_user(request, f"Successfully sent {success_count} article(s) to review.", level=messages.SUCCESS)
        if error_count > 0:
            self.message_user(request, f"Failed to send {error_count} article(s) to review.", level=messages.ERROR)
    admin_send_to_review.short_description = "Send to review (DESK_CHECK → UNDER_REVIEW)"
    
    def admin_request_revision(self, request, queryset):
        """Request revision (UNDER_REVIEW → REVISION_REQUIRED)."""
        if not request.user.is_superuser:
            self.message_user(request, "Only superadmins can perform workflow actions.", level=messages.ERROR)
            return
        
        service = ArticleWorkflowService()
        success_count = 0
        error_count = 0
        
        for article in queryset:
            try:
                service.request_revision(article, request.user, 'MAJOR', 'Revision requested via admin panel')
                success_count += 1
            except ValidationError as e:
                self.message_user(request, f"Article {article.submission_id}: {str(e)}", level=messages.ERROR)
                error_count += 1
        
        if success_count > 0:
            self.message_user(request, f"Successfully requested revision for {success_count} article(s).", level=messages.SUCCESS)
        if error_count > 0:
            self.message_user(request, f"Failed to request revision for {error_count} article(s).", level=messages.ERROR)
    admin_request_revision.short_description = "Request revision (UNDER_REVIEW → REVISION_REQUIRED)"
    
    def admin_accept_article(self, request, queryset):
        """Accept articles (UNDER_REVIEW → ACCEPTED, creates invoice if APC required)."""
        if not request.user.is_superuser:
            self.message_user(request, "Only superadmins can perform workflow actions.", level=messages.ERROR)
            return
        
        service = ArticleWorkflowService()
        success_count = 0
        error_count = 0
        
        for article in queryset:
            try:
                service.accept_article(article, request.user, 'Article accepted via admin panel')
                success_count += 1
            except ValidationError as e:
                self.message_user(request, f"Article {article.submission_id}: {str(e)}", level=messages.ERROR)
                error_count += 1
        
        if success_count > 0:
            self.message_user(request, f"Successfully accepted {success_count} article(s). Invoice created if APC required.", level=messages.SUCCESS)
        if error_count > 0:
            self.message_user(request, f"Failed to accept {error_count} article(s).", level=messages.ERROR)
    admin_accept_article.short_description = "Accept article (UNDER_REVIEW → ACCEPTED)"
    
    def admin_reject_article(self, request, queryset):
        """Reject articles (UNDER_REVIEW → REJECTED)."""
        if not request.user.is_superuser:
            self.message_user(request, "Only superadmins can perform workflow actions.", level=messages.ERROR)
            return
        
        service = ArticleWorkflowService()
        success_count = 0
        error_count = 0
        
        for article in queryset:
            try:
                service.reject_article(article, request.user, 'Article rejected via admin panel')
                success_count += 1
            except ValidationError as e:
                self.message_user(request, f"Article {article.submission_id}: {str(e)}", level=messages.ERROR)
                error_count += 1
        
        if success_count > 0:
            self.message_user(request, f"Successfully rejected {success_count} article(s).", level=messages.SUCCESS)
        if error_count > 0:
            self.message_user(request, f"Failed to reject {error_count} article(s).", level=messages.ERROR)
    admin_reject_article.short_description = "Reject article (UNDER_REVIEW → REJECTED)"
    
    def admin_desk_reject(self, request, queryset):
        """Desk reject articles (DESK_CHECK/SUBMITTED → REJECTED)."""
        if not request.user.is_superuser:
            self.message_user(request, "Only superadmins can perform workflow actions.", level=messages.ERROR)
            return
        
        service = ArticleWorkflowService()
        success_count = 0
        error_count = 0
        
        for article in queryset:
            try:
                service.desk_reject(article, request.user, 'Desk rejected via admin panel')
                success_count += 1
            except ValidationError as e:
                self.message_user(request, f"Article {article.submission_id}: {str(e)}", level=messages.ERROR)
                error_count += 1
        
        if success_count > 0:
            self.message_user(request, f"Successfully desk rejected {success_count} article(s).", level=messages.SUCCESS)
        if error_count > 0:
            self.message_user(request, f"Failed to desk reject {error_count} article(s).", level=messages.ERROR)
    admin_desk_reject.short_description = "Desk reject (DESK_CHECK/SUBMITTED → REJECTED)"
    
    def admin_move_to_production(self, request, queryset):
        """Move articles to production (ACCEPTED → PRODUCTION, requires payment gate)."""
        if not request.user.is_superuser:
            self.message_user(request, "Only superadmins can perform workflow actions.", level=messages.ERROR)
            return
        
        service = ArticleWorkflowService()
        success_count = 0
        error_count = 0
        
        for article in queryset:
            try:
                service.move_to_production(article, request.user)
                success_count += 1
            except ValidationError as e:
                self.message_user(request, f"Article {article.submission_id}: {str(e)}", level=messages.ERROR)
                error_count += 1
        
        if success_count > 0:
            self.message_user(request, f"Successfully moved {success_count} article(s) to production.", level=messages.SUCCESS)
        if error_count > 0:
            self.message_user(request, f"Failed to move {error_count} article(s) to production. Check payment status.", level=messages.ERROR)
    admin_move_to_production.short_description = "Move to production (ACCEPTED → PRODUCTION, payment gate)"
    
    def admin_publish_article(self, request, queryset):
        """Publish articles (ACCEPTED/PRODUCTION → PUBLISHED, requires payment gate)."""
        if not request.user.is_superuser:
            self.message_user(request, "Only superadmins can perform workflow actions.", level=messages.ERROR)
            return
        
        service = ArticleWorkflowService()
        success_count = 0
        error_count = 0
        
        for article in queryset:
            try:
                service.publish_article(article, request.user, publication_url='')
                success_count += 1
            except ValidationError as e:
                self.message_user(request, f"Article {article.submission_id}: {str(e)}", level=messages.ERROR)
                error_count += 1
        
        if success_count > 0:
            self.message_user(request, f"Successfully published {success_count} article(s).", level=messages.SUCCESS)
        if error_count > 0:
            self.message_user(request, f"Failed to publish {error_count} article(s). Check payment status.", level=messages.ERROR)
    admin_publish_article.short_description = "Publish article (ACCEPTED/PRODUCTION → PUBLISHED, payment gate)"


@admin.register(ArticleVersion)
class ArticleVersionAdmin(admin.ModelAdmin):
    list_display = ('article', 'version_number', 'revision_type', 'created_at', 'created_by')
    list_filter = ('revision_type', 'created_at')
    search_fields = ('article__submission_id', 'article__title')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('article', 'reviewer', 'recommendation', 'created_at')
    list_filter = ('recommendation', 'created_at')
    search_fields = ('article__submission_id', 'reviewer__email')

