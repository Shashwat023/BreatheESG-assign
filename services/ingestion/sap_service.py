"""
SAP Fuel/Procurement Ingestion Service.

Handles the messy reality of SAP CSV exports:
- Multiple plants with different column name conventions (English vs German)
- Mixed date formats across exports (ISO, European, German, US)
- Mixed units (liters and gallons in same file)
- Blank/invalid values in quantity fields
- Leading/trailing whitespace in plant codes

The service reads raw CSV data into RawRecord verbatim (including messy columns).
The NormalizationEngine handles unit conversion and date parsing.

Column mapping (from DataSource.column_mapping) allows per-source configuration.
Default mapping handles the known column variants.
"""
import csv
import io
import logging
from services.ingestion.base import IngestionServiceBase

logger = logging.getLogger(__name__)

# Default SAP column name mappings (source → canonical)
# Handles both German SAP exports and English exports
DEFAULT_COLUMN_MAPPING = {
    # German field names (common in SAP for European plants)
    'Buchungsdatum': 'date',
    'Werk': 'plant_code',
    'Material': 'material_code',
    'Materialkurztext': 'fuel_type_description',
    'Menge': 'quantity',
    'ME': 'unit',
    'Kostenart': 'cost_element',
    'Kostenstelle': 'cost_center',
    'Betrag': 'amount',
    # English field names (common in SAP for UK/US plants)
    'Date': 'date',
    'Plant Code': 'plant_code',
    'Fuel Type': 'material_code',
    'Description': 'fuel_type_description',
    'Qty': 'quantity',
    'Unit': 'unit',
    'Cost Element': 'cost_element',
    'Cost Center': 'cost_center',
    'Total Cost (GBP)': 'amount',
    # Other common variants
    'Booking Date': 'date',
    'Plant': 'plant_code',
    'Quantity': 'quantity',
    'UoM': 'unit',
}

# Known fuel type mappings (material code → readable name)
FUEL_TYPE_MAP = {
    'DIESEL-A': 'Diesel',
    'PETROL-B': 'Petrol',
    'NATGAS': 'Natural Gas',
    'LPG': 'LPG',
    'HFO': 'Heavy Fuel Oil',
}


class SAPIngestionService(IngestionServiceBase):
    """
    Ingestion service for SAP fuel/procurement CSV exports.

    Reads CSV, applies column mapping (from DataSource.column_mapping or defaults),
    strips whitespace from values, and stores each row verbatim in RawRecord.

    The raw_data dict stored in RawRecord uses canonical column names
    (post-mapping) so the NormalizationEngine can work consistently regardless
    of which SAP plant generated the export.
    """

    def get_source_type(self) -> str:
        return 'sap'

    def _get_column_mapping(self) -> dict:
        """Get column mapping from DataSource config or fall back to defaults."""
        if self.data_source and self.data_source.column_mapping:
            # DataSource.column_mapping overrides defaults for per-source configuration
            return {**DEFAULT_COLUMN_MAPPING, **self.data_source.column_mapping}
        return DEFAULT_COLUMN_MAPPING

    def _map_row(self, row: dict, mapping: dict) -> dict:
        """
        Apply column mapping to a row dict.
        Returns new dict with canonical column names.
        Strips whitespace from all string values.
        Preserves unmapped columns with their original names.
        """
        mapped = {}
        for source_col, value in row.items():
            # Strip whitespace from column names (SAP sometimes adds trailing spaces)
            clean_col = source_col.strip()
            # Strip whitespace from string values
            if isinstance(value, str):
                value = value.strip()
            # Map to canonical name if known, otherwise keep original
            canonical_col = mapping.get(clean_col, clean_col)
            mapped[canonical_col] = value
        return mapped

    def parse_source(self, file_or_data) -> list:
        """
        Parse SAP CSV export into a list of row dicts.

        Handles:
        - File object or string input
        - UTF-8 and Latin-1 encoding (SAP sometimes exports Latin-1)
        - BOM (byte order mark) in UTF-8 files
        - Skips completely empty rows
        """
        mapping = self._get_column_mapping()
        rows = []

        # Handle file object or string
        if hasattr(file_or_data, 'read'):
            content = file_or_data.read()
            if isinstance(content, bytes):
                # Try UTF-8 first, fall back to Latin-1
                try:
                    content = content.decode('utf-8-sig')  # utf-8-sig handles BOM
                except UnicodeDecodeError:
                    content = content.decode('latin-1')
            file_like = io.StringIO(content)
        else:
            file_like = io.StringIO(str(file_or_data))

        reader = csv.DictReader(file_like)

        for row in reader:
            # Skip completely empty rows
            if all(v.strip() == '' for v in row.values() if isinstance(v, str)):
                continue

            # Apply column mapping
            mapped_row = self._map_row(dict(row), mapping)

            # Enrich with readable fuel type name if possible
            if 'material_code' in mapped_row and mapped_row['material_code'] in FUEL_TYPE_MAP:
                mapped_row['fuel_type'] = FUEL_TYPE_MAP[mapped_row['material_code']]

            rows.append(mapped_row)

        logger.info(f'SAP parser: read {len(rows)} rows from {getattr(file_or_data, "name", "input")}')
        return rows
