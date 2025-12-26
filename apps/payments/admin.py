from django.contrib import admin
from .models import Invoice, Payment


class PaymentInline(admin.TabularInline):
    """Inline admin for payment records."""
    model = Payment
    extra = 0
    readonly_fields = ('provider_transaction_id', 'provider', 'amount', 'currency', 'status', 'created_at', 'completed_at')
    fields = ('provider', 'provider_transaction_id', 'amount', 'currency', 'status', 'created_at', 'completed_at')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'article', 'amount', 'currency', 'status', 'article_payment_status', 'article_status', 'payment_provider', 'created_at')
    list_filter = ('status', 'payment_provider', 'currency')
    search_fields = ('invoice_number', 'article__submission_id', 'article__title')
    readonly_fields = ('invoice_number', 'article_payment_status', 'article_status', 'created_at', 'updated_at', 'paid_at')
    inlines = [PaymentInline]
    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice_number', 'article', 'amount', 'currency', 'status')
        }),
        ('Article Status', {
            'fields': ('article_status', 'article_payment_status'),
            'description': 'Article.status (scientific workflow) and Article.payment_status (business workflow) are tracked separately. Payment operations update payment_status, not Article.status.'
        }),
        ('Payment Provider', {
            'fields': ('payment_provider', 'provider_transaction_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'paid_at')
        }),
    )
    
    def article_payment_status(self, obj):
        """Display article payment status."""
        return obj.article.get_payment_status()
    article_payment_status.short_description = 'Article Payment Status'
    article_payment_status.admin_order_field = 'article__payment_status'
    
    def article_status(self, obj):
        """Display article scientific workflow status."""
        return obj.article.status
    article_status.short_description = 'Article Status (Scientific)'
    article_status.admin_order_field = 'article__status'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('article', 'article__journal', 'article__corresponding_author')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('provider_transaction_id', 'invoice', 'provider', 'amount', 'currency', 'status', 'created_at')
    list_filter = ('status', 'provider', 'currency')
    search_fields = ('provider_transaction_id', 'invoice__invoice_number')
    readonly_fields = ('created_at', 'updated_at', 'completed_at')

