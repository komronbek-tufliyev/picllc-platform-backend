"""
Celery tasks for certificate generation.
"""
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import qrcode
from io import BytesIO
from PIL import Image

from .models import Certificate
from apps.articles.models import Article
from apps.audit.models import AuditLog


@shared_task
def generate_certificate_pdf(certificate_id):
    """
    Generate PDF certificate for a published article.
    
    Args:
        certificate_id: UUID of the certificate
    """
    try:
        certificate = Certificate.objects.get(certificate_id=certificate_id)
        article = certificate.article
        
        # Verify article is published
        if article.status != 'PUBLISHED':
            raise ValueError(f"Article {article.submission_id} is not published.")
        
        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1E4FD8'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=colors.HexColor('#2C2C2C'),
            spaceAfter=20,
            alignment=TA_CENTER
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=12,
            textColor=colors.HexColor('#2C2C2C'),
            alignment=TA_LEFT,
            spaceAfter=15
        )
        
        # Title
        story.append(Spacer(1, 40*mm))
        story.append(Paragraph(
            settings.CERTIFICATE_ISSUER_NAME,
            title_style
        ))
        story.append(Spacer(1, 20*mm))
        
        # Certificate heading
        story.append(Paragraph("Certificate of Publication", heading_style))
        story.append(Spacer(1, 30*mm))
        
        # Certificate content
        content = f"""
        This is to certify that the article entitled<br/><br/>
        <b>"{article.title}"</b><br/><br/>
        by {', '.join([author.get('name', '') for author in article.authors[:3]])}<br/><br/>
        has been published in<br/><br/>
        <b>{article.journal.name}</b><br/><br/>
        Submission ID: {article.submission_id}<br/>
        Publication Date: {article.publication_date.strftime('%B %d, %Y') if article.publication_date else 'N/A'}<br/>
        """
        
        story.append(Paragraph(content, body_style))
        story.append(Spacer(1, 30*mm))
        
        # QR Code
        verification_url = certificate.verification_url
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(verification_url)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        # Add QR code image
        from reportlab.platypus import Image as ReportLabImage
        qr_image = ReportLabImage(qr_buffer, width=80*mm, height=80*mm)
        story.append(qr_image)
        story.append(Spacer(1, 10*mm))
        
        # Certificate ID
        story.append(Paragraph(
            f"Certificate ID: {certificate.certificate_id}",
            ParagraphStyle(
                'CertificateID',
                parent=styles['BodyText'],
                fontSize=10,
                textColor=colors.HexColor('#666666'),
                alignment=TA_CENTER
            )
        ))
        
        # Build PDF
        doc.build(story)
        
        # Save PDF to certificate
        buffer.seek(0)
        certificate.pdf_file.save(
            f'certificate-{certificate.certificate_id}.pdf',
            buffer,
            save=False
        )
        certificate.save()
        
        # Log certificate generation
        AuditLog.objects.create(
            actor=None,  # System action
            action='CERTIFICATE_ISSUED',
            entity_type='CERTIFICATE',
            entity_id=certificate.id,
            metadata={
                'certificate_id': str(certificate.certificate_id),
                'article_submission_id': article.submission_id
            }
        )
        
        # Update article status to CERTIFICATE_ISSUED
        if article.status == 'PUBLISHED':
            article.transition_status(
                article.current_status_enum,
                'SYSTEM',
                user=None
            )
            # Manually set to CERTIFICATE_ISSUED
            article.status = 'CERTIFICATE_ISSUED'
            article.save()
        
        # Send email notification
        from apps.notifications.tasks import send_certificate_ready_email
        send_certificate_ready_email.delay(str(certificate.certificate_id))
        
        return f"Certificate generated successfully: {certificate.certificate_id}"
        
    except Certificate.DoesNotExist:
        return f"Certificate not found: {certificate_id}"
    except Exception as e:
        return f"Error generating certificate: {str(e)}"


@shared_task
def auto_generate_certificate(article_id):
    """
    Auto-generate certificate when article is published.
    
    Args:
        article_id: ID of the published article
    """
    try:
        article = Article.objects.get(id=article_id)
        
        if article.status != 'PUBLISHED':
            return f"Article {article.submission_id} is not published."
        
        # Check if certificate already exists
        if hasattr(article, 'certificate'):
            return f"Certificate already exists for article {article.submission_id}"
        
        # Create certificate
        certificate = Certificate.objects.create(
            article=article,
            status=Certificate.Status.ACTIVE
        )
        
        # Generate PDF
        generate_certificate_pdf.delay(str(certificate.certificate_id))
        
        return f"Certificate creation initiated for article {article.submission_id}"
        
    except Article.DoesNotExist:
        return f"Article not found: {article_id}"
    except Exception as e:
        return f"Error creating certificate: {str(e)}"

