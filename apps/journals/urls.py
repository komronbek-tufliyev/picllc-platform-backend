"""
URLs for journals.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JournalViewSet, ReviewerJournalAssignmentViewSet

router = DefaultRouter()
router.register(r'', JournalViewSet, basename='journal')
router.register(r'assignments', ReviewerJournalAssignmentViewSet, basename='reviewer-assignment')

urlpatterns = router.urls
