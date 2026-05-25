from django.contrib import admin
from .models import DataSource, RawUpload, RawRecord


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'source_type', 'is_active', 'created_at']
    list_filter = ['source_type', 'organization', 'is_active']
    search_fields = ['name', 'organization__name']


@admin.register(RawUpload)
class RawUploadAdmin(admin.ModelAdmin):
    list_display = [
        'organization', 'source_type', 'original_filename', 'status',
        'total_rows', 'successful_rows', 'failed_rows', 'ingestion_timestamp'
    ]
    list_filter = ['source_type', 'status', 'organization']
    readonly_fields = ['ingestion_timestamp']


@admin.register(RawRecord)
class RawRecordAdmin(admin.ModelAdmin):
    list_display = ['upload', 'source_row_number', 'validation_status', 'created_at']
    list_filter = ['validation_status', 'organization']
    readonly_fields = ['raw_data', 'created_at']
