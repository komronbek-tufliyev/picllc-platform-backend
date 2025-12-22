"""
Journal models.
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Journal(models.Model):
    """
    Journal model representing a publication journal.
    """
    name = models.CharField(max_length=255, unique=True)
    issn = models.CharField(max_length=20, unique=True, blank=True)
    scope = models.TextField(help_text='Journal scope and description')
    
    # APC Configuration
    apc_enabled = models.BooleanField(
        default=True,
        help_text='Whether APC payment is required for this journal'
    )
    apc_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Article Processing Charge amount'
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        help_text='Currency code (e.g., USD, UZS)'
    )
    
    # Media
    logo = models.ImageField(upload_to='journals/logos/', blank=True, null=True)
    
    # Publication
    publication_base_url = models.URLField(
        blank=True,
        help_text='Base URL for published articles (optional)'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'journals'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class ReviewerJournalAssignment(models.Model):
    """
    Assignment of Reviewers to specific Journals.
    """
    reviewer = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='journal_assignments',
        limit_choices_to={'role': 'REVIEWER'}
    )
    journal = models.ForeignKey(
        Journal,
        on_delete=models.CASCADE,
        related_name='reviewer_assignments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reviewer_journal_assignments'
        unique_together = ['reviewer', 'journal']
    
    def __str__(self):
        return f"{self.reviewer.email} -> {self.journal.name}"

