"""
Celery tasks for email notifications.
"""
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from apps.articles.models import Article
from apps.payments.models import Invoice
from apps.certificates.models import Certificate


@shared_task
def send_article_submitted_email(article_id):
    """Send email notification when article is submitted."""
    try:
        article = Article.objects.get(id=article_id)
        author = article.corresponding_author
        
        subject = f'Article Submitted: {article.submission_id}'
        message = f"""
        Dear {author.first_name or author.email},
        
        Your article "{article.title}" has been successfully submitted to {article.journal.name}.
        
        Submission ID: {article.submission_id}
        
        You can track the status of your article in your dashboard.
        
        Best regards,
        {settings.CERTIFICATE_ISSUER_NAME}
        """
        
        send_mail(
            subject,
            strip_tags(message),
            settings.DEFAULT_FROM_EMAIL,
            [author.email],
            fail_silently=False,
        )
        
        return f"Email sent to {author.email}"
    except Exception as e:
        return f"Error sending email: {str(e)}"


@shared_task
def send_revision_requested_email(article_id, reviewer_comments):
    """Send email when revision is requested."""
    try:
        article = Article.objects.get(id=article_id)
        author = article.corresponding_author
        
        subject = f'Revision Requested: {article.submission_id}'
        message = f"""
        Dear {author.first_name or author.email},
        
        The reviewers have requested revisions for your article "{article.title}".
        
        Submission ID: {article.submission_id}
        
        Comments from reviewers:
        {reviewer_comments}
        
        Please submit your revised manuscript through your dashboard.
        
        Best regards,
        {settings.CERTIFICATE_ISSUER_NAME}
        """
        
        send_mail(
            subject,
            strip_tags(message),
            settings.DEFAULT_FROM_EMAIL,
            [author.email],
            fail_silently=False,
        )
        
        return f"Revision request email sent to {author.email}"
    except Exception as e:
        return f"Error sending email: {str(e)}"


@shared_task
def send_article_accepted_email(article_id):
    """Send email when article is accepted."""
    try:
        article = Article.objects.get(id=article_id)
        author = article.corresponding_author
        
        subject = f'Article Accepted: {article.submission_id}'
        message = f"""
        Dear {author.first_name or author.email},
        
        Congratulations! Your article "{article.title}" has been accepted for publication in {article.journal.name}.
        
        Submission ID: {article.submission_id}
        
        """
        
        # Add payment information if APC is required
        if article.journal.apc_enabled and article.journal.apc_amount > 0:
            message += f"""
            Article Processing Charge: {article.journal.apc_amount} {article.journal.currency}
            
            Please proceed with payment to complete the publication process.
            """
        
        message += """
        
        Best regards,
        {settings.CERTIFICATE_ISSUER_NAME}
        """
        
        send_mail(
            subject,
            strip_tags(message),
            settings.DEFAULT_FROM_EMAIL,
            [author.email],
            fail_silently=False,
        )
        
        return f"Acceptance email sent to {author.email}"
    except Exception as e:
        return f"Error sending email: {str(e)}"


@shared_task
def send_article_rejected_email(article_id, reviewer_comments):
    """Send email when article is rejected."""
    try:
        article = Article.objects.get(id=article_id)
        author = article.corresponding_author
        
        subject = f'Article Decision: {article.submission_id}'
        message = f"""
        Dear {author.first_name or author.email},
        
        We regret to inform you that your article "{article.title}" has not been accepted for publication.
        
        Submission ID: {article.submission_id}
        
        Comments from reviewers:
        {reviewer_comments}
        
        Thank you for your submission.
        
        Best regards,
        {settings.CERTIFICATE_ISSUER_NAME}
        """
        
        send_mail(
            subject,
            strip_tags(message),
            settings.DEFAULT_FROM_EMAIL,
            [author.email],
            fail_silently=False,
        )
        
        return f"Rejection email sent to {author.email}"
    except Exception as e:
        return f"Error sending email: {str(e)}"


@shared_task
def send_payment_confirmation_email(invoice_id):
    """Send email when payment is confirmed."""
    try:
        invoice = Invoice.objects.get(id=invoice_id)
        article = invoice.article
        author = article.corresponding_author
        
        subject = f'Payment Confirmed: {invoice.invoice_number}'
        message = f"""
        Dear {author.first_name or author.email},
        
        Your payment for article "{article.title}" has been confirmed.
        
        Invoice Number: {invoice.invoice_number}
        Amount: {invoice.amount} {invoice.currency}
        
        Your article will proceed to publication.
        
        Best regards,
        {settings.CERTIFICATE_ISSUER_NAME}
        """
        
        send_mail(
            subject,
            strip_tags(message),
            settings.DEFAULT_FROM_EMAIL,
            [author.email],
            fail_silently=False,
        )
        
        return f"Payment confirmation email sent to {author.email}"
    except Exception as e:
        return f"Error sending email: {str(e)}"


@shared_task
def send_article_published_email(article_id):
    """Send email when article is published."""
    try:
        article = Article.objects.get(id=article_id)
        author = article.corresponding_author
        
        subject = f'Article Published: {article.submission_id}'
        message = f"""
        Dear {author.first_name or author.email},
        
        Your article "{article.title}" has been published in {article.journal.name}.
        
        Submission ID: {article.submission_id}
        Publication URL: {article.publication_url}
        
        Your certificate is available for download in your dashboard.
        
        Best regards,
        {settings.CERTIFICATE_ISSUER_NAME}
        """
        
        send_mail(
            subject,
            strip_tags(message),
            settings.DEFAULT_FROM_EMAIL,
            [author.email],
            fail_silently=False,
        )
        
        return f"Publication email sent to {author.email}"
    except Exception as e:
        return f"Error sending email: {str(e)}"


@shared_task
def send_certificate_ready_email(certificate_id):
    """Send email when certificate is ready."""
    try:
        certificate = Certificate.objects.get(certificate_id=certificate_id)
        article = certificate.article
        author = article.corresponding_author
        
        subject = f'Certificate Ready: {article.submission_id}'
        message = f"""
        Dear {author.first_name or author.email},
        
        Your certificate for article "{article.title}" is now available.
        
        Submission ID: {article.submission_id}
        Certificate ID: {certificate.certificate_id}
        
        You can download your certificate from your dashboard.
        
        Best regards,
        {settings.CERTIFICATE_ISSUER_NAME}
        """
        
        send_mail(
            subject,
            strip_tags(message),
            settings.DEFAULT_FROM_EMAIL,
            [author.email],
            fail_silently=False,
        )
        
        return f"Certificate ready email sent to {author.email}"
    except Exception as e:
        return f"Error sending email: {str(e)}"

