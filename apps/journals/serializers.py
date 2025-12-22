"""
Serializers for journals.
"""
from rest_framework import serializers
from .models import Journal, ReviewerJournalAssignment


class JournalSerializer(serializers.ModelSerializer):
    """Serializer for Journal model."""
    
    class Meta:
        model = Journal
        fields = [
            'id', 'name', 'issn', 'scope', 'apc_enabled', 'apc_amount',
            'currency', 'logo', 'publication_base_url', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class JournalListSerializer(serializers.ModelSerializer):
    """Simplified serializer for journal lists."""
    
    class Meta:
        model = Journal
        fields = [
            'id', 'name', 'issn', 'scope', 'apc_enabled', 'apc_amount',
            'currency', 'logo', 'is_active'
        ]


class ReviewerJournalAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for Reviewer-Journal assignments."""
    reviewer_email = serializers.EmailField(source='reviewer.email', read_only=True)
    journal_name = serializers.CharField(source='journal.name', read_only=True)
    
    class Meta:
        model = ReviewerJournalAssignment
        fields = ['id', 'reviewer', 'reviewer_email', 'journal', 'journal_name', 'created_at']
        read_only_fields = ['id', 'created_at']

