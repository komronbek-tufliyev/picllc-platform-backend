"""
Role-based permissions for UJMP.
"""
from rest_framework import permissions


class IsAuthor(permissions.BasePermission):
    """Permission class to check if user is an Author."""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'AUTHOR'
        )


class IsReviewer(permissions.BasePermission):
    """Permission class to check if user is a Reviewer."""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'REVIEWER'
        )


class IsAdmin(permissions.BasePermission):
    """Permission class to check if user is an Admin."""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'ADMIN'
        )


class IsAuthorOrAdmin(permissions.BasePermission):
    """Permission class to check if user is Author or Admin."""
    
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ['AUTHOR', 'ADMIN']
        )


class IsReviewerOrAdmin(permissions.BasePermission):
    """Permission class to check if user is Reviewer or Admin."""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['REVIEWER', 'ADMIN']
        )


class IsAuthorOrReviewerOrAdmin(permissions.BasePermission):
    """Permission class to check if user is Author, Reviewer, or Admin."""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['AUTHOR', 'REVIEWER', 'ADMIN']
        )

