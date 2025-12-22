from django.contrib import admin
from .models import Journal, ReviewerJournalAssignment


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ('name', 'issn', 'apc_enabled', 'apc_amount', 'currency', 'is_active', 'created_at')
    list_filter = ('is_active', 'apc_enabled')
    search_fields = ('name', 'issn')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'issn', 'scope', 'logo', 'is_active')
        }),
        ('APC Configuration', {
            'fields': ('apc_enabled', 'apc_amount', 'currency')
        }),
        ('Publication', {
            'fields': ('publication_base_url',)
        }),
    )


@admin.register(ReviewerJournalAssignment)
class ReviewerJournalAssignmentAdmin(admin.ModelAdmin):
    list_display = ('reviewer', 'journal', 'created_at')
    list_filter = ('journal', 'created_at')
    search_fields = ('reviewer__email', 'journal__name')

