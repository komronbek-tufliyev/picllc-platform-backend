"""
Serializers for audit logs.
"""
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from .models import AuditLog
from apps.accounts.serializers import UserSerializer


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog."""
    actor_email = serializers.EmailField(source='actor.email', read_only=True, allow_null=True)
    actor_name = serializers.SerializerMethodField()
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'actor', 'actor_email', 'actor_name', 'action',
            'entity_type', 'entity_id', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_actor_name(self, obj) -> str:
        """Get actor's full name, email, or 'SYSTEM'."""
        if obj.actor:
            return f"{obj.actor.first_name} {obj.actor.last_name}".strip() or obj.actor.email
        return 'SYSTEM'

