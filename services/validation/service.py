"""
Validation Service.

Responsible for detecting anomalies in normalized data.
Key feature: Statistical anomaly detection within an upload batch.
If one record has vastly different CO2e than the rest of the batch,
it is flagged as 'suspicious' for analyst review.
"""
import logging
from decimal import Decimal
from django.db.models import Avg, StdDev
from apps.normalization.models import NormalizedEmissionRecord

logger = logging.getLogger(__name__)

class ValidationService:
    @staticmethod
    def flag_suspicious_records(upload_id: int, threshold_sigma: float = 3.0) -> int:
        """
        Flag records in a batch where CO2e deviates significantly from the mean.
        
        Args:
            upload_id: The RawUpload ID
            threshold_sigma: Number of standard deviations to consider anomalous
            
        Returns:
            Number of records flagged
        """
        records = NormalizedEmissionRecord.objects.filter(
            upload_id=upload_id,
            status='pending_review'
        )
        
        if records.count() < 5:
            # Not enough data for meaningful statistics
            return 0
            
        stats = records.aggregate(
            mean_co2e=Avg('co2e'),
            std_dev=StdDev('co2e')
        )
        
        mean = stats['mean_co2e']
        std_dev = stats['std_dev'] or Decimal('0')
        
        if not mean or std_dev == 0:
            return 0
            
        # Upper threshold for anomaly
        threshold = mean + (Decimal(str(threshold_sigma)) * std_dev)
        
        # Also flag zero or negative CO2e as universally suspicious
        suspicious_qs = records.filter(co2e__gt=threshold) | records.filter(co2e__lte=0)
        
        flagged_count = suspicious_qs.update(is_suspicious=True)
        logger.info(f"Flagged {flagged_count} suspicious records in upload {upload_id}")
        
        return flagged_count

    @staticmethod
    def validate_travel_distances(upload_id: int) -> int:
        """
        Specifically flag travel records with missing or anomalous distances.
        """
        records = NormalizedEmissionRecord.objects.filter(
            upload_id=upload_id,
            source_type='travel',
            status='pending_review'
        )
        
        flagged = 0
        for record in records:
            # E.g. flight distance > 20000km is impossible (half earth circumference)
            if record.activity_unit == 'passenger-km' and record.activity_value > 20000:
                record.is_suspicious = True
                record.save(update_fields=['is_suspicious'])
                flagged += 1
                
        return flagged
