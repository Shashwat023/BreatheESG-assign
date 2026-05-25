import pytest
from decimal import Decimal
from apps.organizations.models import Organization
from apps.ingestion.models import RawUpload, RawRecord, DataSource
from apps.normalization.models import EmissionFactor, UnitConversion, NormalizedEmissionRecord
from services.ingestion.sap_service import SAPIngestionService
from services.normalization.engine import NormalizationEngine
from services.validation.service import ValidationService

@pytest.mark.django_db
class TestIngestionAndNormalization:

    @pytest.fixture
    def setup_data(self):
        # 1. Create Organization
        org, _ = Organization.objects.get_or_create(name="Test Org", slug="test-org")

        # 2. Create Data Source
        data_source, _ = DataSource.objects.get_or_create(
            organization=org,
            name="SAP Export",
            source_type="sap"
        )

        # 3. Create Unit Conversions
        UnitConversion.objects.get_or_create(
            from_unit="gallon",
            to_unit="liter",
            defaults={"conversion_factor": Decimal("3.78541200")}
        )
        UnitConversion.objects.get_or_create(
            from_unit="MWh",
            to_unit="kWh",
            defaults={"conversion_factor": Decimal("1000.00000000")}
        )

        # 4. Create Emission Factors
        EmissionFactor.objects.get_or_create(
            category="Fuel Combustion - Diesel",
            scope="scope_1",
            activity_unit="liter",
            year=2023,
            defaults={"factor_value": Decimal("2.680000"), "factor_source": "DEFRA 2023"}
        )
        EmissionFactor.objects.get_or_create(
            category="Electricity - UK Grid",
            scope="scope_2",
            activity_unit="kWh",
            year=2023,
            defaults={"factor_value": Decimal("0.212330"), "factor_source": "DEFRA 2023"}
        )

        return org, data_source

    def test_sap_parsing(self, setup_data):
        org, data_source = setup_data
        service = SAPIngestionService(organization=org, data_source=data_source)
        
        # Test parsing a simple SAP CSV structure
        csv_data = (
            "Date,Plant Code,Fuel Type,Description,Qty,Unit,Total Cost (GBP)\n"
            "2023-01-15,PLT-01,DIESEL-A,Diesel Fuel,150,gallon,300.00\n"
        )
        
        parsed_rows = service.parse_source(csv_data)
        assert len(parsed_rows) == 1
        row = parsed_rows[0]
        assert row["plant_code"] == "PLT-01"
        assert row["material_code"] == "DIESEL-A"
        assert row["quantity"] == "150"
        assert row["unit"] == "gallon"
        assert row["fuel_type"] == "Diesel"

    def test_normalization_engine(self, setup_data):
        org, data_source = setup_data
        
        # Create a raw upload
        upload = RawUpload.objects.create(
            organization=org,
            data_source=data_source,
            source_type="sap",
            original_filename="sap_test.csv"
        )
        
        # Create raw record with mapped fields
        raw_record = RawRecord.objects.create(
            organization=org,
            upload=upload,
            source_row_number=1,
            raw_data={
                "date": "2023-01-15",
                "plant_code": "PLT-01",
                "material_code": "DIESEL-A",
                "quantity": "100.00",
                "unit": "gallon",
                "category": "Fuel Combustion - Diesel"
            },
            validation_status="valid"
        )
        
        engine = NormalizationEngine()
        norm_record = engine.normalize_record(raw_record)
        
        assert norm_record is not None
        assert norm_record.category == "Fuel Combustion - Diesel"
        assert norm_record.scope == "scope_1"
        # 100 gallons = 378.5412 liters
        assert norm_record.normalized_value == Decimal("378.5412")
        assert norm_record.normalized_unit == "liter"
        # CO2e = 378.5412 * 2.68 = 1014.490416 -> truncated/rounded by database constraints
        assert round(norm_record.co2e, 2) == round(Decimal("378.5412") * Decimal("2.68"), 2)

    def test_validation_service_anomaly(self, setup_data):
        org, data_source = setup_data
        
        # Create an upload
        upload = RawUpload.objects.create(
            organization=org,
            data_source=data_source,
            source_type="sap",
            original_filename="sap_batch_test.csv"
        )
        
        factor = EmissionFactor.objects.get(category="Fuel Combustion - Diesel", year=2023)
        
        # Create 5 records, 4 normal and 1 massive outlier
        # Normal records: 10 liters (26.8 kg CO2e)
        for i in range(4):
            raw = RawRecord.objects.create(
                organization=org, upload=upload, source_row_number=i+1, raw_data={}, validation_status="valid"
            )
            NormalizedEmissionRecord.objects.create(
                organization=org,
                raw_record=raw,
                upload=upload,
                source_type="sap",
                scope="scope_1",
                category="Fuel Combustion - Diesel",
                activity_value=Decimal("10"),
                activity_unit="liter",
                normalized_value=Decimal("10"),
                normalized_unit="liter",
                emission_factor=factor,
                emission_factor_value=factor.factor_value,
                co2e=Decimal("26.8"),
                status="pending_review"
            )
            
        # Outlier: 1000 liters (2680 kg CO2e)
        outlier_raw = RawRecord.objects.create(
            organization=org, upload=upload, source_row_number=5, raw_data={}, validation_status="valid"
        )
        outlier_norm = NormalizedEmissionRecord.objects.create(
            organization=org,
            raw_record=outlier_raw,
            upload=upload,
            source_type="sap",
            scope="scope_1",
            category="Fuel Combustion - Diesel",
            activity_value=Decimal("1000"),
            activity_unit="liter",
            normalized_value=Decimal("1000"),
            normalized_unit="liter",
            emission_factor=factor,
            emission_factor_value=factor.factor_value,
            co2e=Decimal("2680.0"),
            status="pending_review"
        )
        
        # Run statistical validation
        flagged = ValidationService.flag_suspicious_records(upload.id, threshold_sigma=1.0)
        
        assert flagged > 0
        outlier_norm.refresh_from_db()
        assert outlier_norm.is_suspicious is True

