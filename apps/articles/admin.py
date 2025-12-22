from django.contrib import admin
from .models import Article, ArticleVersion, Review


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('submission_id', 'title', 'journal', 'corresponding_author', 'status', 'created_at')
    list_filter = ('status', 'journal', 'created_at')
    search_fields = ('submission_id', 'title', 'corresponding_author__email')
    readonly_fields = ('submission_id', 'created_at', 'updated_at', 'submitted_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('submission_id', 'title', 'abstract', 'keywords', 'journal')
        }),
        ('Authors', {
            'fields': ('corresponding_author', 'authors')
        }),
        ('Workflow', {
            'fields': ('status', 'submitted_at')
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

