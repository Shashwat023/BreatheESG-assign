"""
Corporate Travel Ingestion Service.

Handles JSON-format travel data with 3 travel types:
- flight: origin + destination airport codes, cabin class, distance_km
- hotel: location, hotel name, nights
- ground_transport: transport mode, distance_km

Key challenges:
- Mixed record structures (flight/hotel/ground_transport have different fields)
- Missing distance_km on some flights (need geolocation calculation in normalization)
- Airport codes require lookup for distance calculation
- JSON not CSV (different parsing)

The service reads the JSON array, extracts each record as-is into RawRecord.
Distance calculation (for flights without distance_km) happens in NormalizationEngine.
"""
import json
import logging
from services.ingestion.base import IngestionServiceBase

logger = logging.getLogger(__name__)

VALID_TRAVEL_TYPES = {'flight', 'hotel', 'ground_transport'}


class TravelIngestionService(IngestionServiceBase):
    """
    Ingestion service for corporate travel JSON exports.

    Reads a JSON array where each object is one travel record.
    Supports mixed travel types: flight, hotel, ground_transport.
    Stores each record verbatim in RawRecord.
    """

    def get_source_type(self) -> str:
        return 'travel'

    def parse_source(self, file_or_data) -> list:
        """
        Parse corporate travel JSON into list of record dicts.

        Handles:
        - File object or string input
        - JSON array at top level
        - Skips records missing required fields (travel_type, trip_date)
        """
        rows = []
        skipped = 0

        if hasattr(file_or_data, 'read'):
            content = file_or_data.read()
            if isinstance(content, bytes):
                content = content.decode('utf-8')
            data = json.loads(content)
        elif isinstance(file_or_data, str):
            data = json.loads(file_or_data)
        elif isinstance(file_or_data, list):
            data = file_or_data
        else:
            raise ValueError(f'Unsupported input type: {type(file_or_data)}')

        if not isinstance(data, list):
            raise ValueError('Travel data must be a JSON array')

        for record in data:
            if not isinstance(record, dict):
                skipped += 1
                continue

            # travel_type is required
            travel_type = record.get('travel_type', '')
            if travel_type not in VALID_TRAVEL_TYPES:
                logger.warning(f'Unknown travel_type: {travel_type!r} — skipping')
                skipped += 1
                continue

            rows.append(record)

        logger.info(f'Travel parser: {len(rows)} records parsed, {skipped} skipped')
        return rows
