"""
Signals for article lifecycle events.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Article
from .workflow import ArticleStatus
from apps.certificates.tasks import auto_generate_certificate


@receiver(post_save, sender=Article)
def handle_article_status_change(sender, instance, created, **kwargs):
    """
    Handle article status changes and trigger appropriate actions.
    """
    if created:
        return  # Skip on creation
    
    # Auto-generate certificate when article is published
    if instance.status == ArticleStatus.PUBLISHED.value:
        auto_generate_certificate.delay(instance.id)

