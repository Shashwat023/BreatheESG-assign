"""
Base ingestion service.

All source-specific ingestion services extend IngestionServiceBase.
The base class provides:
- create_upload() — creates the RawUpload batch record
- finalize_upload() — updates status and row counts after processing
- process_row() — abstract method subclasses must implement
- ingest() — main orchestration method

Design principle: raw data is written to RawRecord BEFORE any validation
or transformation. Even rows that fail validation are stored verbatim.
This ensures we never lose source data.
"""
from abc import ABC, abstractmethod
from django.utils import timezone
from apps.ingestion.models import RawUpload, RawRecord
from apps.organizations.models import Organization


class IngestionServiceBase(ABC):
    """
    Abstract base class for all ingestion services.

    Subclasses must implement:
    - parse_source(file_or_data) → list of dicts (one dict per row)
    - get_source_type() → str ('sap', 'utility', 'travel')

    Subclasses may override:
    - pre_process_row(row_dict) → row_dict (for normalization before storage)
    """

    def __init__(self, organization: Organization, data_source=None):
        self.organization = organization
        self.data_source = data_source
        self._upload = None

    def get_source_type(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def parse_source(self, file_or_data) -> list:
        """
        Parse the source file or data into a list of raw row dicts.

        Return value: list of dicts, one dict per source row.
        Keys should be the original column names from the source.
        Values should be strings exactly as they appear in the source.
        """
        pass

    def create_upload(self, filename: str = '', file_path: str = '') -> RawUpload:
        """Create the RawUpload batch record. Called before row processing."""
        self._upload = RawUpload.objects.create(
            organization=self.organization,
            data_source=self.data_source,
            source_type=self.get_source_type(),
            original_filename=filename,
            file_path=file_path,
            status='processing',
        )
        return self._upload

    def store_record(self, row_number: int, raw_data: dict,
                     validation_status: str = 'valid',
                     error_detail=None) -> RawRecord:
        """Store a single raw row into RawRecord. Called per row."""
        return RawRecord.objects.create(
            organization=self.organization,
            upload=self._upload,
            source_row_number=row_number,
            raw_data=raw_data,
            validation_status=validation_status,
            error_detail=error_detail,
        )

    def finalize_upload(self, total: int, successful: int, failed: int,
                        status: str = 'complete', notes: str = ''):
        """Update RawUpload with final row counts and status."""
        if self._upload:
            self._upload.total_rows = total
            self._upload.successful_rows = successful
            self._upload.failed_rows = failed
            self._upload.status = status
            self._upload.notes = notes
            self._upload.save(update_fields=[
                'total_rows', 'successful_rows', 'failed_rows', 'status', 'notes'
            ])

    def ingest(self, file_or_data, filename: str = '', file_path: str = '') -> dict:
        """
        Main ingestion orchestration method.

        Parses source, creates upload batch, stores all rows (including failures),
        and finalizes the upload with counts.

        Returns:
            {
                'upload_id': int,
                'total_rows': int,
                'successful_rows': int,
                'failed_rows': int,
                'errors': list of {row: int, error: str}
            }
        """
        # Create the batch record
        upload = self.create_upload(filename=filename, file_path=file_path)

        # Parse all rows from the source
        try:
            rows = self.parse_source(file_or_data)
        except Exception as e:
            self.finalize_upload(0, 0, 0, status='failed', notes=f'Parse error: {e}')
            return {
                'upload_id': upload.id,
                'total_rows': 0,
                'successful_rows': 0,
                'failed_rows': 0,
                'errors': [{'row': 0, 'error': f'Parse error: {e}'}]
            }

        total = len(rows)
        successful = 0
        failed = 0
        errors = []

        # Process each row individually — a row failure must not stop the batch
        for i, raw_row in enumerate(rows, start=1):
            try:
                # Store verbatim — validation happens in a later service
                self.store_record(
                    row_number=i,
                    raw_data=raw_row,
                    validation_status='valid',
                )
                successful += 1
            except Exception as e:
                failed += 1
                errors.append({'row': i, 'error': str(e)})

        self.finalize_upload(
            total=total,
            successful=successful,
            failed=failed,
            status='complete' if failed < total else 'failed',
        )

        return {
            'upload_id': upload.id,
            'total_rows': total,
            'successful_rows': successful,
            'failed_rows': failed,
            'errors': errors,
        }
