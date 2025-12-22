from django.contrib import admin
from .models import Invoice, Payment


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'article', 'amount', 'currency', 'status', 'payment_provider', 'created_at')
    list_filter = ('status', 'payment_provider', 'currency')
    search_fields = ('invoice_number', 'article__submission_id', 'article__title')
    readonly_fields = ('invoice_number', 'created_at', 'updated_at', 'paid_at')
    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice_number', 'article', 'amount', 'currency', 'status')
        }),
        ('Payment Provider', {
            'fields': ('payment_provider', 'provider_transaction_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'paid_at')
        }),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('provider_transaction_id', 'invoice', 'provider', 'amount', 'currency', 'status', 'created_at')
    list_filter = ('status', 'provider', 'currency')
    search_fields = ('provider_transaction_id', 'invoice__invoice_number')
    readonly_fields = ('created_at', 'updated_at', 'completed_at')

