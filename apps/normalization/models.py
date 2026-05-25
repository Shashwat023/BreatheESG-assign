"""
Normalization models — the unified CO2e emission record and its supporting tables.

Design principles:
1. SNAPSHOT PATTERN: emission_factor_value is denormalized onto NormalizedEmissionRecord.
   If the EmissionFactor record changes in future (e.g., updated DEFRA factors),
   historical CO2e calculations remain correct. We always know what factor was used.

2. FULL TRACEABILITY: raw_record → upload → data_source → organization.
   Every normalized record can be traced to its exact source row.

3. SCOPE MAPPING: scope (1/2/3) is assigned systematically from a category→scope
   lookup, not from free-text. This prevents inconsistency across sources.
"""
from django.db import models
from apps.organizations.models import Organization
from apps.ingestion.models import RawRecord, RawUpload, DataSource


class EmissionFactor(models.Model):
    """
    CO2e emission factor per activity unit.

    Seeded from DEFRA 2023 / EPA GHG Protocol standard factors.
    Stored per category, unit, year, and source for full traceability.

    Formula: CO2e (kg) = activity_value × factor_value

    Examples:
    - Diesel combustion: 2.68 kg CO2e per liter (DEFRA 2023)
    - UK grid electricity: 0.21233 kg CO2e per kWh (DEFRA 2023)
    - Long-haul flight: 0.19548 kg CO2e per passenger-km (DEFRA 2023)
    """
    SCOPE_CHOICES = [
        ('scope_1', 'Scope 1 — Direct Emissions'),
        ('scope_2', 'Scope 2 — Indirect (Electricity)'),
        ('scope_3', 'Scope 3 — Value Chain'),
    ]

    category = models.CharField(
        max_length=255,
        help_text="Activity category (e.g., 'Fuel Combustion - Diesel', 'Electricity - UK Grid')"
    )
    subcategory = models.CharField(max_length=255, blank=True)
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES)
    activity_unit = models.CharField(
        max_length=50,
        help_text="Unit of the activity value (e.g., 'liter', 'kWh', 'passenger-km', 'night')"
    )
    # kg CO2e per activity unit
    factor_value = models.DecimalField(
        max_digits=12, decimal_places=6,
        help_text="Emission factor in kg CO2e per activity unit"
    )
    factor_source = models.CharField(
        max_length=255,
        help_text="Publication source of this factor (e.g., 'DEFRA 2023', 'EPA GHG 2023')"
    )
    year = models.IntegerField(help_text="Year this emission factor applies to")
    region = models.CharField(
        max_length=100, default='global',
        help_text="Geographic region this factor applies to (e.g., 'UK', 'US', 'global')"
    )
    gwp_version = models.CharField(
        max_length=50, default='AR5',
        help_text="IPCC Assessment Report GWP version (AR4, AR5, AR6)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scope', 'category']

    def __str__(self):
        return (
            f"{self.category} — {self.factor_value} kg CO2e/{self.activity_unit} "
            f"({self.factor_source}, {self.year})"
        )


class UnitConversion(models.Model):
    """
    Unit conversion factors for normalizing activity values.

    Centralizes all unit math to prevent conversion drift.
    All conversions in the system go through this table.

    Examples:
    - MWh → kWh: multiply by 1000
    - gallon → liter: multiply by 3.78541
    - ton → kg: multiply by 1000
    - mile → km: multiply by 1.60934
    """
    from_unit = models.CharField(max_length=50)
    to_unit = models.CharField(max_length=50)
    conversion_factor = models.DecimalField(
        max_digits=15, decimal_places=8,
        help_text="Multiply from_unit value by this factor to get to_unit value"
    )
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ['from_unit', 'to_unit']
        ordering = ['from_unit', 'to_unit']

    def __str__(self):
        return f"1 {self.from_unit} = {self.conversion_factor} {self.to_unit}"


class NormalizedEmissionRecord(models.Model):
    """
    The unified emission record — the heart of the system.

    Every ingestion source (SAP fuel, utility electricity, corporate travel)
    maps into this single schema. Analysts review and approve these records.

    The schema matches the required output format:
    {organization, source_type, scope, category, activity_value, activity_unit,
     normalized_value, normalized_unit, emission_factor, co2e, status}

    Key design decisions:
    - emission_factor FK + emission_factor_value (denormalized): snapshot pattern
    - is_manually_edited: tracks post-normalization changes for audit
    - is_suspicious: set by ValidationService when CO2e is anomalous
    - metadata JSONField: captures source-specific context (plant codes, meter IDs, etc.)
    """
    STATUS_CHOICES = [
        ('pending_review', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('needs_clarification', 'Needs Clarification'),
    ]

    SCOPE_CHOICES = [
        ('scope_1', 'Scope 1 — Direct Emissions'),
        ('scope_2', 'Scope 2 — Indirect (Electricity)'),
        ('scope_3', 'Scope 3 — Value Chain'),
    ]

    # ---- Multi-tenancy ----
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='normalized_records'
    )

    # ---- Source traceability chain ----
    # raw_record → upload → data_source → organization
    raw_record = models.OneToOneField(
        RawRecord, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='normalized',
        help_text="The raw source row this normalized record was derived from"
    )
    upload = models.ForeignKey(
        RawUpload, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='normalized_records',
        help_text="The upload batch this record belongs to"
    )
    data_source = models.ForeignKey(
        DataSource, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='normalized_records'
    )
    source_type = models.CharField(
        max_length=50,
        help_text="Source system type: 'sap', 'utility', or 'travel'"
    )

    # ---- Emission classification ----
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES)
    category = models.CharField(
        max_length=255,
        help_text="Activity category (e.g., 'Fuel Combustion - Diesel')"
    )
    subcategory = models.CharField(max_length=255, blank=True)

    # ---- Activity data (as reported by source) ----
    activity_value = models.DecimalField(
        max_digits=15, decimal_places=4,
        help_text="Quantity of activity as reported by the source"
    )
    activity_unit = models.CharField(
        max_length=50,
        help_text="Unit as reported by the source (may be non-canonical, e.g., 'MWh', 'gallon')"
    )

    # ---- Normalized data (after unit conversion) ----
    normalized_value = models.DecimalField(
        max_digits=15, decimal_places=4,
        help_text="Quantity converted to the canonical unit for this category"
    )
    normalized_unit = models.CharField(
        max_length=50,
        help_text="Canonical unit for this category (e.g., 'kWh' for electricity, 'liter' for fuel)"
    )

    # ---- CO2e calculation (snapshot pattern) ----
    emission_factor = models.ForeignKey(
        EmissionFactor, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="The emission factor record used at calculation time"
    )
    # Denormalized snapshot of factor value at calculation time.
    # If EmissionFactor.factor_value changes in future, historical CO2e remains correct.
    emission_factor_value = models.DecimalField(
        max_digits=12, decimal_places=6, null=True, blank=True,
        help_text="Snapshot of the factor value (kg CO2e/unit) used at calculation time"
    )
    # CO2e = normalized_value × emission_factor_value
    co2e = models.DecimalField(
        max_digits=15, decimal_places=4, null=True, blank=True,
        help_text="Calculated CO2e in kg. Formula: normalized_value × emission_factor_value"
    )

    # ---- Review workflow ----
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default='pending_review'
    )
    is_suspicious = models.BooleanField(
        default=False,
        help_text=(
            "True if CO2e value is anomalous vs batch mean (flagged by ValidationService). "
            "Analysts should review these first."
        )
    )
    is_manually_edited = models.BooleanField(
        default=False,
        help_text="True if this record was edited after initial normalization. Triggers AuditLog entry."
    )

    # ---- Temporal metadata ----
    period_start = models.DateField(
        null=True, blank=True,
        help_text="Start of the activity period (billing period start, travel date, etc.)"
    )
    period_end = models.DateField(
        null=True, blank=True,
        help_text="End of the activity period"
    )

    # ---- Source-specific context ----
    # Captures fields specific to each source type without adding columns:
    # SAP: {"plant_code": "PLT-001", "material_code": "DIESEL-A"}
    # Utility: {"meter_id": "MTR-12345", "tariff": "Business Standard"}
    # Travel: {"origin_airport": "LHR", "destination_airport": "JFK", "distance_km": 5540}
    metadata = models.JSONField(
        default=dict,
        help_text="Source-specific metadata (plant codes, meter IDs, airport codes, etc.)"
    )

    # ---- Timestamps ----
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'scope']),
            models.Index(fields=['organization', 'source_type']),
            models.Index(fields=['is_suspicious']),
        ]

    def __str__(self):
        return (
            f"{self.organization.name} | {self.get_scope_display()} | "
            f"{self.category} | {self.co2e} kg CO2e ({self.status})"
        )
