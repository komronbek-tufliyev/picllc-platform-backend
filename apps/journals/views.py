"""
API views for journals.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import Journal, ReviewerJournalAssignment
from .serializers import (
    JournalSerializer,
    JournalListSerializer,
    ReviewerJournalAssignmentSerializer
)
from apps.accounts.permissions import IsAdmin, IsReviewerOrAdmin


class JournalViewSet(viewsets.ModelViewSet):
    """
    ViewSet for journals.
    
    - Public: Can list and view journals
    - Admins: Full CRUD access
    """
    queryset = Journal.objects.filter(is_active=True)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['apc_enabled']
    search_fields = ['name', 'issn', 'scope']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return JournalListSerializer
        return JournalSerializer
    
    def get_permissions(self):
        """Public read access, admin write access."""
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdmin()]
    
    def get_queryset(self):
        """Filter active journals for public, all for admin."""
        if self.request.user.is_authenticated and self.request.user.role == 'ADMIN':
            return Journal.objects.all()
        return Journal.objects.filter(is_active=True)


class ReviewerJournalAssignmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for reviewer-journal assignments.
    
    - Admins: Full CRUD access
    """
    queryset = ReviewerJournalAssignment.objects.select_related(
        'reviewer', 'journal'
    ).all()
    serializer_class = ReviewerJournalAssignmentSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['reviewer', 'journal']

