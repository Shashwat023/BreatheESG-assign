---
phase: 1
plan: "01-02"
status: complete
completed: 2026-05-25
---

# Summary: 01-02 Core Data Models

## What was built

All 9 core Django models defined with full FK relationships and admin registration:

### Models Created

| App | Model | Key Fields |
|-----|-------|-----------|
| organizations | **Organization** | name, slug, is_active |
| ingestion | **DataSource** | organization FK, source_type, column_mapping (JSON) |
| ingestion | **RawUpload** | organization FK, source_type, status, total/successful/failed rows |
| ingestion | **RawRecord** | upload FK, raw_data (JSON), validation_status, error_detail (JSON) |
| normalization | **EmissionFactor** | category, scope, factor_value, activity_unit, factor_source |
| normalization | **UnitConversion** | from_unit, to_unit, conversion_factor |
| normalization | **NormalizedEmissionRecord** | Full CO2e schema + traceability chain + snapshot pattern |
| audit | **AuditLog** | model_name, object_id, action, old_value, new_value, actor |
| emissions | **ReviewStatus** | emission_record FK, status, previous_status, reviewer |

### Key Design Decisions Implemented

- **NormalizedEmissionRecord**: emission_factor FK + emission_factor_value (denormalized snapshot) ensures historical CO2e values remain correct even if factors update
- **RawRecord**: raw_data JSONField preserves verbatim source rows — immutable after creation
- **AuditLog**: Admin set to read-only (no add/change/delete) to protect audit trail integrity
- **Multi-tenancy**: Organization FK present on Organization, RawUpload, RawRecord, NormalizedEmissionRecord, AuditLog, ReviewStatus

## Key files created

- `apps/organizations/models.py` + `admin.py`
- `apps/ingestion/models.py` + `admin.py`
- `apps/normalization/models.py` + `admin.py`
- `apps/audit/models.py` + `admin.py`
- `apps/emissions/models.py` + `admin.py`
- `apps/*/migrations/0001_initial.py` (5 migration files)

## Migration result

All 5 migrations created successfully. PostgreSQL not running locally — migrations cannot be applied yet but migration files are correct. `python manage.py makemigrations` exits with 0 issues (warnings about DB connection are expected without local PostgreSQL).

## Deviations from plan

None — all 9 models implemented as specified.
