"""
Management command: seed_data

Loads sample organizations, emission factors, and unit conversions into the database.
Run with: python manage.py seed_data

This command is idempotent — running it multiple times won't create duplicates.
Uses get_or_create() for all objects.
"""
import json
from pathlib import Path
from django.core.management.base import BaseCommand
from apps.organizations.models import Organization
from apps.normalization.models import EmissionFactor, UnitConversion


FACTORS_FILE = Path(__file__).resolve().parent.parent.parent.parent.parent.parent / 'data' / 'emission_factors' / 'factors.json'


SAMPLE_ORGANIZATIONS = [
    {'name': 'ABC Corporation', 'slug': 'abc-corporation'},
    {'name': 'XYZ Manufacturing Ltd', 'slug': 'xyz-manufacturing-ltd'},
    {'name': 'Greenfield Logistics', 'slug': 'greenfield-logistics'},
]

UNIT_CONVERSIONS = [
    # Energy
    {'from_unit': 'MWh', 'to_unit': 'kWh', 'conversion_factor': '1000.00000000', 'notes': 'Megawatt-hours to kilowatt-hours'},
    {'from_unit': 'kWh', 'to_unit': 'MWh', 'conversion_factor': '0.00100000', 'notes': 'Kilowatt-hours to megawatt-hours'},
    # Volume
    {'from_unit': 'gallon', 'to_unit': 'liter', 'conversion_factor': '3.78541200', 'notes': 'US gallon to liter'},
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
    help = 'Seed the database with sample organizations, emission factors, and unit conversions'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')

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

        # Emission factors
        if not FACTORS_FILE.exists():
            self.stdout.write(self.style.WARNING(f'  Emission factors file not found: {FACTORS_FILE}'))
        else:
            with open(FACTORS_FILE) as f:
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

        self.stdout.write(self.style.SUCCESS('Seed complete!'))
