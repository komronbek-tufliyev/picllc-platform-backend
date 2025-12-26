"""
URLs for journals.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JournalViewSet, ReviewerJournalAssignmentViewSet

router = DefaultRouter()
# Register more specific routes first to avoid conflicts
router.register(r'assignments', ReviewerJournalAssignmentViewSet, basename='reviewer-assignment')
router.register(r'', JournalViewSet, basename='journal')

urlpatterns = router.urls
