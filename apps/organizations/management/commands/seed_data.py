"""
Management command: seed_data

Loads sample organizations, emission factors, and unit conversions into the database.
Also ingests and normalizes the mock datasets for ABC Corporation to prepare a full reviewer-ready environment.
Run with: python manage.py seed_data

This command is idempotent — running it multiple times won't create duplicates.
Uses get_or_create() for objects and clears/re-ingests the raw uploads for ABC Corporation.
"""
import json
import logging
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from apps.organizations.models import Organization
from apps.normalization.models import EmissionFactor, UnitConversion, NormalizedEmissionRecord
from apps.ingestion.models import DataSource, RawUpload, RawRecord
from apps.emissions.models import ReviewStatus
from apps.audit.models import AuditLog

from services.ingestion.sap_service import SAPIngestionService
from services.ingestion.utility_service import UtilityIngestionService
from services.ingestion.travel_service import TravelIngestionService
from services.normalization.engine import NormalizationEngine
from services.validation.service import ValidationService

logger = logging.getLogger(__name__)

# Base DIR relative paths
FACTORS_FILE = settings.BASE_DIR / 'data' / 'emission_factors' / 'factors.json'
SAP_FILE = settings.BASE_DIR / 'data' / 'mock_datasets' / 'sap_fuel_export.csv'
UTILITY_FILE = settings.BASE_DIR / 'data' / 'mock_datasets' / 'utility_electricity.csv'
TRAVEL_FILE = settings.BASE_DIR / 'data' / 'mock_datasets' / 'corporate_travel.json'

SAMPLE_ORGANIZATIONS = [
    {'name': 'ABC Corporation', 'slug': 'abc-corporation'},
    {'name': 'XYZ Manufacturing Ltd', 'slug': 'xyz-manufacturing-ltd'},
    {'name': 'Greenfield Logistics', 'slug': 'greenfield-logistics'},
]

UNIT_CONVERSIONS = [
    # Energy
    {'from_unit': 'MWh', 'to_unit': 'kWh', 'conversion_factor': '1000.00000000', 'notes': 'Megawatt-hours to kilowatt-hours'},
    {'from_unit': 'kWh', 'to_unit': 'MWh', 'conversion_factor': '0.00100000', 'notes': 'Kilowatt-hours to megawatt-hours'},
    {'from_unit': 'mwh', 'to_unit': 'kWh', 'conversion_factor': '1000.00000000', 'notes': 'mwh to kWh'},
    {'from_unit': 'kwh', 'to_unit': 'kWh', 'conversion_factor': '1.00000000', 'notes': 'kwh to kWh'},
    # Volume
    {'from_unit': 'gallon', 'to_unit': 'liter', 'conversion_factor': '3.78541200', 'notes': 'US gallon to liter'},
    {'from_unit': 'gal', 'to_unit': 'liter', 'conversion_factor': '3.78541200', 'notes': 'gal to liter'},
    {'from_unit': 'l', 'to_unit': 'liter', 'conversion_factor': '1.00000000', 'notes': 'l to liter'},
    {'from_unit': 'imperial_gallon', 'to_unit': 'liter', 'conversion_factor': '4.54609000', 'notes': 'Imperial gallon to liter'},
    {'from_unit': 'liter', 'to_unit': 'gallon', 'conversion_factor': '0.26417200', 'notes': 'Liter to US gallon'},
    # Distance
    {'from_unit': 'mile', 'to_unit': 'km', 'conversion_factor': '1.60934000', 'notes': 'Miles to kilometers'},
    {'from_unit': 'km', 'to_unit': 'mile', 'conversion_factor': '0.62137100', 'notes': 'Kilometers to miles'},
    # Mass
    {'from_unit': 'ton', 'to_unit': 'kg', 'conversion_factor': '1000.00000000', 'notes': 'Metric ton to kilograms'},
    {'from_unit': 'tonne', 'to_unit': 'kg', 'conversion_factor': '1000.00000000', 'notes': 'Tonne to kilograms'},
    # Identity conversions (already canonical units)
    {'from_unit': 'liter', 'to_unit': 'liter', 'conversion_factor': '1.00000000', 'notes': 'Identity'},
    {'from_unit': 'kWh', 'to_unit': 'kWh', 'conversion_factor': '1.00000000', 'notes': 'Identity'},
    {'from_unit': 'km', 'to_unit': 'km', 'conversion_factor': '1.00000000', 'notes': 'Identity'},
    {'from_unit': 'm3', 'to_unit': 'm3', 'conversion_factor': '1.00000000', 'notes': 'Identity'},
    {'from_unit': 'night', 'to_unit': 'night', 'conversion_factor': '1.00000000', 'notes': 'Identity'},
    {'from_unit': 'passenger-km', 'to_unit': 'passenger-km', 'conversion_factor': '1.00000000', 'notes': 'Identity'},
]



class Command(BaseCommand):
    help = 'Seed the database with sample organizations, factors, unit conversions, and mock datasets'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')

        # Defensive logging of resolved file paths
        files_to_check = {
            "Emission Factors JSON": FACTORS_FILE,
            "SAP Fuel CSV": SAP_FILE,
            "Utility Electricity CSV": UTILITY_FILE,
            "Corporate Travel JSON": TRAVEL_FILE,
        }

        self.stdout.write("Resolving file paths defensively:")
        for name, path in files_to_check.items():
            self.stdout.write(f"  {name} resolved to: {path}")
            if not path.exists():
                self.stderr.write(self.style.ERROR(f"CRITICAL: Required file '{name}' is missing at: {path}"))
                raise CommandError(f"Seeding failed: File '{name}' not found at {path}")
            self.stdout.write(self.style.SUCCESS(f"  Verified: {name} exists!"))

        # Organizations
        orgs_created = 0
        for org_data in SAMPLE_ORGANIZATIONS:
            _, created = Organization.objects.get_or_create(
                slug=org_data['slug'],
                defaults={'name': org_data['name']}
            )
            if created:
                orgs_created += 1
        self.stdout.write(f'  Organizations: {orgs_created} created, {len(SAMPLE_ORGANIZATIONS) - orgs_created} already existed')

        # Get ABC Corporation reference
        abc_org = Organization.objects.get(slug='abc-corporation')

        # Clean up existing uploads for ABC Corporation to maintain idempotency
        deleted_records, _ = NormalizedEmissionRecord.objects.filter(organization=abc_org).delete()
        deleted_reviews, _ = ReviewStatus.objects.filter(organization=abc_org).delete()
        deleted_uploads, _ = RawUpload.objects.filter(organization=abc_org).delete()
        deleted_logs, _ = AuditLog.objects.filter(organization=abc_org).delete()

        if deleted_uploads > 0:
            self.stdout.write(f"  Cleared {deleted_uploads} existing uploads, {deleted_records} records, {deleted_reviews} reviews, and {deleted_logs} audit logs for ABC Corporation.")

        # Data Sources for ABC Corporation
        sap_ds, _ = DataSource.objects.get_or_create(
            organization=abc_org,
            source_type='sap',
            defaults={'name': 'SAP Fuel Export'}
        )
        utility_ds, _ = DataSource.objects.get_or_create(
            organization=abc_org,
            source_type='utility',
            defaults={'name': 'Utility Electricity bills'}
        )
        travel_ds, _ = DataSource.objects.get_or_create(
            organization=abc_org,
            source_type='travel',
            defaults={'name': 'Corporate Travel API'}
        )

        # Emission factors
        with open(FACTORS_FILE, 'r', encoding='utf-8') as f:
            factors = json.load(f)
        factors_created = 0
        for factor_data in factors:
            _, created = EmissionFactor.objects.get_or_create(
                category=factor_data['category'],
                subcategory=factor_data.get('subcategory', ''),
                scope=factor_data['scope'],
                activity_unit=factor_data['activity_unit'],
                year=factor_data['year'],
                defaults={
                    'factor_value': factor_data['factor_value'],
                    'factor_source': factor_data['factor_source'],
                    'region': factor_data.get('region', 'global'),
                    'gwp_version': factor_data.get('gwp_version', 'AR5'),
                }
            )
            if created:
                factors_created += 1
        self.stdout.write(f'  Emission factors: {factors_created} created, {len(factors) - factors_created} already existed')

        # Unit conversions
        conversions_created = 0
        for conv_data in UNIT_CONVERSIONS:
            _, created = UnitConversion.objects.get_or_create(
                from_unit=conv_data['from_unit'],
                to_unit=conv_data['to_unit'],
                defaults={
                    'conversion_factor': conv_data['conversion_factor'],
                    'notes': conv_data.get('notes', ''),
                }
            )
            if created:
                conversions_created += 1
        self.stdout.write(f'  Unit conversions: {conversions_created} created')

        # --- Mock Datasets Ingestion & Normalization ---

        # 1. Ingest SAP Fuel CSV
        self.stdout.write("Ingesting SAP Fuel CSV...")
        sap_service = SAPIngestionService(organization=abc_org, data_source=sap_ds)
        with open(SAP_FILE, 'r', encoding='utf-8') as f:
            sap_res = sap_service.ingest(f, filename='sap_fuel_export.csv')
        sap_upload_id = sap_res['upload_id']
        self.stdout.write(f"  SAP Ingestion: Created Upload ID {sap_upload_id} ({sap_res['successful_rows']} rows)")

        # 2. Ingest Utility Electricity CSV
        self.stdout.write("Ingesting Utility Electricity CSV...")
        utility_service = UtilityIngestionService(organization=abc_org, data_source=utility_ds)
        with open(UTILITY_FILE, 'r', encoding='utf-8') as f:
            utility_res = utility_service.ingest(f, filename='utility_electricity.csv')
        utility_upload_id = utility_res['upload_id']
        self.stdout.write(f"  Utility Ingestion: Created Upload ID {utility_upload_id} ({utility_res['successful_rows']} rows)")

        # 3. Ingest Corporate Travel JSON
        self.stdout.write("Ingesting Corporate Travel JSON...")
        travel_service = TravelIngestionService(organization=abc_org, data_source=travel_ds)
        with open(TRAVEL_FILE, 'r', encoding='utf-8') as f:
            travel_res = travel_service.ingest(f, filename='corporate_travel.json')
        travel_upload_id = travel_res['upload_id']
        self.stdout.write(f"  Travel Ingestion: Created Upload ID {travel_upload_id} ({travel_res['successful_rows']} rows)")

        # Normalize and flag anomalies
        engine = NormalizationEngine()
        
        for upload_id, name in [
            (sap_upload_id, "SAP Fuel"),
            (utility_upload_id, "Utility Electricity"),
            (travel_upload_id, "Corporate Travel"),
        ]:
            self.stdout.write(f"Normalizing upload {name} (ID: {upload_id})...")
            norm_res = engine.normalize_upload(upload_id)
            self.stdout.write(f"  Normalized: {norm_res['success']} succeeded, {norm_res['failed']} failed")

            self.stdout.write(f"Running validation checks for {name} (ID: {upload_id})...")
            flagged_sigma = ValidationService.flag_suspicious_records(upload_id, threshold_sigma=3.0)
            flagged_travel = 0
            if name == "Corporate Travel":
                flagged_travel = ValidationService.validate_travel_distances(upload_id)
            self.stdout.write(f"  Validation flagged: {flagged_sigma} statistical outliers, {flagged_travel} travel distance anomalies")

        # Simulate some record reviews (approvals) to seed review history & audit log updates
        self.stdout.write("Simulating sample analyst approvals...")
        records_to_approve = NormalizedEmissionRecord.objects.filter(
            organization=abc_org,
            is_suspicious=False
        )[:2]
        
        for record in records_to_approve:
            ReviewStatus.objects.create(
                organization=abc_org,
                emission_record=record,
                status='approved',
                previous_status=record.status,
                reviewer='seeder_system',
                notes='Seeded approval for testing'
            )
            record.status = 'approved'
            record.save(update_fields=['status', 'updated_at'])
            
        self.stdout.write(f"  Approved {records_to_approve.count()} records to verify updates & JSON diff audit trails.")
        self.stdout.write(self.style.SUCCESS('Seed complete!'))
