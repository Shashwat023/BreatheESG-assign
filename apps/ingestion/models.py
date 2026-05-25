"""
Ingestion models — track data sources, upload batches, and individual raw records.

Design principle: Raw data is NEVER modified after ingestion. RawRecord preserves
the original source row verbatim. Normalization happens in a separate model
(NormalizedEmissionRecord in the normalization app).

This ensures complete source traceability — every normalized record can always
be traced back to its exact original row in the source file.
"""
from django.db import models
from apps.organizations.models import Organization


class DataSource(models.Model):
    """
    Configuration for a data source (e.g., "SAP Plant A", "Utility Portal - West").

    Stores the column mapping for SAP exports where column names are inconsistent
    between plants and export formats. The column_mapping field lets us configure
    source-specific column names without touching ingestion code.

    Each organization can have multiple data sources of the same type
    (e.g., multiple SAP plants, multiple utility accounts).
    """
    SOURCE_TYPES = [
        ('sap', 'SAP Fuel/Procurement'),
        ('utility', 'Utility Electricity'),
        ('travel', 'Corporate Travel'),
    ]

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='data_sources'
    )
    name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPES)

    # JSON mapping of source column names → canonical column names
    # e.g., {"Fuel Type": "fuel_type", "Plant Code": "plant_code", "Qty (liters)": "quantity"}
    # This handles the reality that SAP exports from different plants use different column headers.
    column_mapping = models.JSONField(
        default=dict,
        help_text=(
            "Maps source column names to canonical field names. "
            "Used to handle messy SAP exports with inconsistent headers."
        )
    )
    metadata = models.JSONField(
        default=dict,
        help_text="Source-specific metadata (plant codes, region, tariff type, etc.)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['organization', 'name']

    def __str__(self):
        return f"{self.organization.name} — {self.name} ({self.source_type})"


class RawUpload(models.Model):
    """
    Represents a single ingestion batch (one CSV upload or one API trigger).

    Before any row is processed, we record the upload metadata here.
    This gives us batch-level traceability: when was this data ingested,
    from what source, and how many rows did it contain?

    Even if normalization fails for individual rows, the upload batch record
    persists — so we can always see what was ingested when.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('complete', 'Complete'),
        ('failed', 'Failed'),
    ]

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='raw_uploads'
    )
    data_source = models.ForeignKey(
        DataSource, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='uploads'
    )
    # Denormalized for quick filtering without joining to DataSource
    source_type = models.CharField(max_length=50)
    original_filename = models.CharField(max_length=500, blank=True)
    file_path = models.CharField(
        max_length=1000, blank=True,
        help_text="Server path where the original uploaded file is stored"
    )
    ingestion_timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    total_rows = models.IntegerField(default=0)
    successful_rows = models.IntegerField(default=0)
    failed_rows = models.IntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-ingestion_timestamp']

    def __str__(self):
        return (
            f"{self.source_type} upload @ {self.ingestion_timestamp:%Y-%m-%d %H:%M} "
            f"({self.organization.name})"
        )


class RawRecord(models.Model):
    """
    One row from the source CSV or API, stored verbatim.

    This is the immutable source of truth. The raw_data JSON field stores
    the original row exactly as it came from the source — column names, values,
    dates, and units are all preserved without transformation.

    The error_detail field captures any parsing/validation issues without
    blocking the rest of the batch. A row with error_detail still gets stored
    here; it just won't be normalized.

    CRITICAL: Never update raw_data after creation. It's a forensic record.
    """
    VALIDATION_STATUS_CHOICES = [
        ('valid', 'Valid'),
        ('failed', 'Validation Failed'),
        ('suspicious', 'Suspicious — Flagged for Review'),
    ]

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='raw_records'
    )
    upload = models.ForeignKey(
        RawUpload, on_delete=models.CASCADE, related_name='records'
    )
    source_row_number = models.IntegerField(
        help_text="Row number in the original source file (1-indexed)"
    )
    # Verbatim copy of the source row. For CSV: {"column_name": "value", ...}
    # For API responses: the original JSON object.
    raw_data = models.JSONField(
        help_text="Original row data preserved verbatim from the source"
    )
    validation_status = models.CharField(
        max_length=50, choices=VALIDATION_STATUS_CHOICES, default='valid'
    )
    # Structured error list, e.g.:
    # [{"field": "date", "error": "Cannot parse '32/13/2024' as a date"},
    #  {"field": "quantity", "error": "Expected number, got 'N/A'"}]
    error_detail = models.JSONField(
        null=True, blank=True,
        help_text=(
            "Structured error list from validation. "
            "Populated only if validation_status is 'failed' or 'suspicious'."
        )
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['upload', 'source_row_number']

    def __str__(self):
        return f"Row {self.source_row_number} of {self.upload}"
