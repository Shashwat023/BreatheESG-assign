from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.ingestion.models import RawUpload, RawRecord
from apps.normalization.models import NormalizedEmissionRecord
from apps.audit.models import AuditLog
from apps.emissions.models import ReviewStatus
from apps.api.serializers import (
    RawUploadSerializer, NormalizedEmissionRecordSerializer,
    AuditLogSerializer, RecordApprovalSerializer
)


class UploadViewSet(viewsets.ReadOnlyModelViewSet):
    """API for viewing ingestion batches."""
    queryset = RawUpload.objects.select_related('organization').order_by('-ingestion_timestamp')
    serializer_class = RawUploadSerializer
    filterset_fields = ['status', 'source_type', 'organization']


class NormalizedRecordViewSet(viewsets.ModelViewSet):
    """
    API for viewing and managing normalized emission records.
    The Section 2 dashboard consumes this.
    """
    serializer_class = NormalizedEmissionRecordSerializer
    filterset_fields = [
        'status', 'scope', 'source_type', 
        'is_suspicious', 'organization'
    ]
    search_fields = ['category', 'subcategory']

    def get_queryset(self):
        queryset = NormalizedEmissionRecord.objects.select_related('organization', 'raw_record').order_by('-created_at')
        org_slug = self.request.query_params.get('org_slug')
        if org_slug:
            queryset = queryset.filter(organization__slug=org_slug)
        return queryset

    @action(detail=True, methods=['post'], serializer_class=RecordApprovalSerializer)
    def review(self, request, pk=None):
        """Analyst workflow to approve/reject a record."""
        record = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_status = serializer.validated_data['status']
        notes = serializer.validated_data.get('notes', '')
        
        # Save history
        ReviewStatus.objects.create(
            organization=record.organization,
            emission_record=record,
            status=new_status,
            previous_status=record.status,
            reviewer='analyst_api',
            notes=notes
        )
        
        # Update record (this will trigger AuditService via signals)
        record.status = new_status
        record.save(update_fields=['status', 'updated_at'])
        
        return Response({'status': 'Review recorded successfully'})


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """API for viewing the immutable audit trail."""
    serializer_class = AuditLogSerializer
    filterset_fields = ['model_name', 'object_id', 'action', 'organization']

    def get_queryset(self):
        queryset = AuditLog.objects.all().order_by('-timestamp')
        org_slug = self.request.query_params.get('org_slug')
        if org_slug:
            queryset = queryset.filter(organization__slug=org_slug)
        return queryset

