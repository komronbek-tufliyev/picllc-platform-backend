"""
User and authentication models.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model with role support.
    
    Roles:
    - AUTHOR: Can submit and manage articles
    - REVIEWER: Can review, decide, and publish articles
    - ADMIN: Platform-level operator
    """
    
    class Role(models.TextChoices):
        AUTHOR = 'AUTHOR', 'Author'
        REVIEWER = 'REVIEWER', 'Reviewer'
        ADMIN = 'ADMIN', 'Admin'
    
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.AUTHOR,
        help_text='User role in the system'
    )
    
    email = models.EmailField(unique=True)
    
    # Optional fields
    phone = models.CharField(max_length=20, blank=True)
    affiliation = models.CharField(max_length=255, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
    
    @property
    def is_author(self):
        return self.role == self.Role.AUTHOR
    
    @property
    def is_reviewer(self):
        return self.role == self.Role.REVIEWER
    
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

