from rest_framework import serializers
from apps.organizations.models import Organization
from apps.ingestion.models import RawUpload, RawRecord, DataSource
from apps.normalization.models import NormalizedEmissionRecord
from apps.audit.models import AuditLog


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name', 'slug']


class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = ['id', 'name', 'source_type']


class RawUploadSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = RawUpload
        fields = [
            'id', 'organization_name', 'source_type', 'original_filename',
            'status', 'total_rows', 'successful_rows', 'failed_rows',
            'ingestion_timestamp', 'notes'
        ]


class RawRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawRecord
        fields = [
            'id', 'source_row_number', 'raw_data', 
            'validation_status', 'error_detail'
        ]


class NormalizedEmissionRecordSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    raw_data = serializers.JSONField(source='raw_record.raw_data', read_only=True)
    error_detail = serializers.JSONField(source='raw_record.error_detail', read_only=True)
    
    class Meta:
        model = NormalizedEmissionRecord
        fields = [
            'id', 'organization_name', 'source_type', 'scope', 'category',
            'subcategory', 'activity_value', 'activity_unit', 
            'normalized_value', 'normalized_unit', 'co2e',
            'status', 'is_suspicious', 'is_manually_edited',
            'period_start', 'period_end', 'metadata',
            'created_at', 'updated_at',
            'raw_data', 'error_detail'
        ]


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            'id', 'model_name', 'object_id', 'action',
            'old_value', 'new_value', 'actor', 'timestamp', 'notes'
        ]


class RecordApprovalSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('needs_clarification', 'Needs Clarification')
    ])
    notes = serializers.CharField(required=False, allow_blank=True)
