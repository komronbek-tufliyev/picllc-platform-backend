"""
API views for certificates.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import Certificate
from .serializers import (
    CertificateSerializer,
    CertificateListSerializer,
    CertificateVerificationSerializer
)
from apps.accounts.permissions import IsAuthor, IsAdmin
from apps.articles.models import Article
from apps.articles.throttling import CertificateVerificationThrottle


class CertificateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for certificates.
    
    - Authors: Can view their own certificates
    - Admins: Can view all certificates and revoke
    """
    queryset = Certificate.objects.select_related('article').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['certificate_id', 'article__submission_id', 'article__title']
    ordering_fields = ['issued_at']
    ordering = ['-issued_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CertificateListSerializer
        return CertificateSerializer
    
    def get_queryset(self):
        """Filter based on user role."""
        user = self.request.user
        
        if user.role == 'AUTHOR':
            # Authors see only certificates for their articles
            return self.queryset.filter(article__corresponding_author=user)
        elif user.role == 'ADMIN':
            # Admins see all certificates
            return self.queryset
        
        return Certificate.objects.none()
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download certificate PDF."""
        certificate = self.get_object()
        
        # Check permissions
        if request.user.role == 'AUTHOR':
            if certificate.article.corresponding_author != request.user:
                return Response(
                    {'error': 'You can only download your own certificates.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        if not certificate.pdf_file:
            return Response(
                {'error': 'Certificate PDF not yet generated.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return FileResponse(
            certificate.pdf_file.open(),
            content_type='application/pdf',
            filename=f'certificate-{certificate.certificate_id}.pdf'
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def revoke(self, request, pk=None):
        """Revoke certificate (Admin only)."""
        certificate = self.get_object()
        
        reason = request.data.get('reason', '')
        
        try:
            certificate.revoke(request.user, reason)
            return Response(
                CertificateSerializer(certificate).data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class CertificateVerificationViewSet(viewsets.ViewSet):
    """
    Public certificate verification endpoint.
    """
    permission_classes = [AllowAny]
    throttle_classes = [CertificateVerificationThrottle]
    serializer_class = CertificateVerificationSerializer
    
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='certificate_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Certificate ID to verify'
            ),
        ],
        responses={
            200: CertificateVerificationSerializer,
            404: OpenApiTypes.OBJECT,
        }
    )
    @action(detail=False, methods=['get'], url_path='(?P<certificate_id>[^/.]+)')
    def verify(self, request, certificate_id=None):
        """Verify certificate by ID."""
        try:
            certificate = get_object_or_404(Certificate, certificate_id=certificate_id)
            
            serializer = CertificateVerificationSerializer({
                'certificate_id': certificate.certificate_id,
                'status': certificate.status,
                'article_title': certificate.article.title,
                'article_submission_id': certificate.article.submission_id,
                'journal_name': certificate.article.journal.name,
                'publication_date': certificate.article.publication_date,
                'publication_url': certificate.article.publication_url,
                'issued_at': certificate.issued_at,
                'revoked': certificate.status == Certificate.Status.REVOKED
            })
            
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': 'Certificate not found or invalid.'},
                status=status.HTTP_404_NOT_FOUND
            )

