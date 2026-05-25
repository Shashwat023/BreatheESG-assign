"""
Utility Electricity Ingestion Service.

Handles electricity billing data from utility providers.
Each row represents one meter's monthly electricity consumption.

Key challenges:
- Mixed units: kWh and MWh in same file (different meters prefer different units)
- Billing period as date range (start + end dates)
- Renewable percentage metadata for green tariffs

The service reads each row verbatim into RawRecord.
Unit conversion (MWh → kWh) happens in the NormalizationEngine.
"""
import csv
import io
import logging
from services.ingestion.base import IngestionServiceBase

logger = logging.getLogger(__name__)


class UtilityIngestionService(IngestionServiceBase):
    """
    Ingestion service for utility electricity CSV exports.

    Reads billing CSV with columns:
    Account_Number, Meter_ID, Site_Name, Billing_Period_Start,
    Billing_Period_End, Energy_Consumed, Unit, Tariff_Code,
    Daily_Rate, Total_Cost_GBP, Supplier, Renewable_Percentage

    Stores each row verbatim in RawRecord with source_type='utility'.
    """

    def get_source_type(self) -> str:
        return 'utility'

    def parse_source(self, file_or_data) -> list:
        """
        Parse utility CSV into list of row dicts.
        Handles file objects and strings.
        Skips empty rows.
        """
        rows = []

        if hasattr(file_or_data, 'read'):
            content = file_or_data.read()
            if isinstance(content, bytes):
                content = content.decode('utf-8-sig')
            file_like = io.StringIO(content)
        else:
            file_like = io.StringIO(str(file_or_data))

        reader = csv.DictReader(file_like)

        for row in reader:
            # Skip empty rows
            if all(v.strip() == '' for v in row.values() if isinstance(v, str)):
                continue

            # Clean whitespace from values
            cleaned = {k.strip(): v.strip() if isinstance(v, str) else v
                       for k, v in row.items()}
            rows.append(cleaned)

        logger.info(f'Utility parser: read {len(rows)} rows')
        return rows
