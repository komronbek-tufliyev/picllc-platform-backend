from django.contrib import admin
from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_id', 'article', 'status', 'issued_at', 'revoked_at', 'revoked_by')
    list_filter = ('status', 'issued_at')
    search_fields = ('certificate_id', 'article__submission_id', 'article__title')
    readonly_fields = ('certificate_id', 'issued_at', 'revoked_at', 'revoked_by')
    fieldsets = (
        ('Certificate Information', {
            'fields': ('certificate_id', 'article', 'status', 'pdf_file')
        }),
        ('Revocation', {
            'fields': ('revoked_at', 'revoked_by', 'revocation_reason')
        }),
        ('Timestamps', {
            'fields': ('issued_at',)
        }),
    )

