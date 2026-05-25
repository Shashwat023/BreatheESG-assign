"""
Normalization Engine.

Core engine that converts raw records into canonical NormalizedEmissionRecord objects.
Responsibilities:
1. Extract fields using source-specific Strategy
2. Convert units using UnitConversion table
3. Assign EmissionFactor based on category and year
4. Calculate CO2e
5. Save NormalizedEmissionRecord
"""
import logging
from decimal import Decimal
from django.db import transaction
from apps.ingestion.models import RawRecord
from apps.normalization.models import (
    NormalizedEmissionRecord, EmissionFactor, UnitConversion
)
from services.normalization.strategies import (
    SAPStrategy, UtilityStrategy, TravelStrategy
)

logger = logging.getLogger(__name__)

class NormalizationEngine:
    def __init__(self):
        self.strategies = {
            'sap': SAPStrategy(),
            'utility': UtilityStrategy(),
            'travel': TravelStrategy(),
        }

    def _convert_unit(self, value: Decimal, from_unit: str, to_unit: str) -> Decimal:
        """Convert value from one unit to another using database rules."""
        if from_unit == to_unit:
            return value
            
        try:
            conversion = UnitConversion.objects.get(
                from_unit=from_unit, to_unit=to_unit
            )
            return value * conversion.conversion_factor
        except UnitConversion.DoesNotExist:
            raise ValueError(f"No unit conversion found for {from_unit} -> {to_unit}")

    def _find_emission_factor(self, category: str, subcategory: str, year: int) -> EmissionFactor:
        """Find the applicable emission factor."""
        # Exact match
        factor = EmissionFactor.objects.filter(
            category=category,
            subcategory=subcategory,
            year=year,
            is_active=True
        ).first()
        
        if factor:
            return factor
            
        # Fallback to category only
        factor = EmissionFactor.objects.filter(
            category=category,
            year=year,
            is_active=True
        ).first()
        
        if factor:
            return factor
            
        # Fallback to most recent year for category
        factor = EmissionFactor.objects.filter(
            category=category,
            is_active=True
        ).order_by('-year').first()
        
        if factor:
            return factor
            
        raise ValueError(f"No emission factor found for category: {category}")

    @transaction.atomic
    def normalize_record(self, raw_record: RawRecord) -> NormalizedEmissionRecord:
        """
        Normalize a single RawRecord.
        If successful, creates a NormalizedEmissionRecord.
        If fails, updates RawRecord.validation_status.
        """
        if raw_record.validation_status != 'valid':
            logger.info(f"Skipping RawRecord {raw_record.id} due to invalid status")
            return None
            
        source_type = raw_record.upload.source_type
        strategy = self.strategies.get(source_type)
        if not strategy:
            raise ValueError(f"No normalization strategy for source_type: {source_type}")

        try:
            # 1. Extract standard fields
            extracted = strategy.extract_fields(raw_record.raw_data)
            
            # 2. Determine year for factor lookup
            year = 2023 # Default
            if extracted.get('period_start'):
                year = extracted['period_start'].year
                
            # 3. Find emission factor
            factor = self._find_emission_factor(
                extracted['category'], 
                extracted.get('subcategory', ''), 
                year
            )
            
            # 4. Convert unit to match factor's activity_unit
            normalized_value = self._convert_unit(
                extracted['activity_value'],
                extracted['activity_unit'],
                factor.activity_unit
            )
            
            # 5. Calculate CO2e
            co2e = normalized_value * factor.factor_value
            
            # 6. Create normalized record
            norm_record = NormalizedEmissionRecord.objects.create(
                organization=raw_record.organization,
                raw_record=raw_record,
                upload=raw_record.upload,
                data_source=raw_record.upload.data_source,
                source_type=source_type,
                scope=factor.scope,
                category=extracted['category'],
                subcategory=extracted.get('subcategory', ''),
                activity_value=extracted['activity_value'],
                activity_unit=extracted['activity_unit'],
                normalized_value=normalized_value,
                normalized_unit=factor.activity_unit,
                emission_factor=factor,
                emission_factor_value=factor.factor_value,
                co2e=co2e,
                period_start=extracted.get('period_start'),
                period_end=extracted.get('period_end'),
                metadata=extracted.get('metadata', {})
            )
            
            return norm_record

        except Exception as e:
            # If normalization fails, mark the raw record as failed
            raw_record.validation_status = 'failed'
            raw_record.error_detail = [{'error': str(e)}]
            raw_record.save(update_fields=['validation_status', 'error_detail'])
            logger.error(f"Failed to normalize RawRecord {raw_record.id}: {e}")
            return None

    def normalize_upload(self, upload_id: int) -> dict:
        """Normalize all valid RawRecords in an upload batch."""
        records = RawRecord.objects.filter(
            upload_id=upload_id, 
            validation_status='valid',
            normalized__isnull=True  # Not already normalized
        )
        
        success = 0
        failed = 0
        
        for raw in records:
            if self.normalize_record(raw):
                success += 1
            else:
                failed += 1
                
        return {'success': success, 'failed': failed}
