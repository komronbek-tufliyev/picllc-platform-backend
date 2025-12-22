from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('UJMP Information', {'fields': ('role', 'phone', 'affiliation')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('UJMP Information', {'fields': ('role', 'phone', 'affiliation')}),
    )

