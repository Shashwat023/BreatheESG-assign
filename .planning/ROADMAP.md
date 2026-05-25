# ROADMAP: breatheESG — Section 1 Backend
# Milestone: v1.0

**Project:** breatheESG ESG Emissions Ingestion Platform
**Milestone:** v1.0 — Core Backend (Section 1)
**Phases:** 5 total
**Requirements mapped:** 43 / 43 ✓

---

## Phase 1: Project Foundation & Data Architecture
**Goal:** Set up Django project structure, configure PostgreSQL, define all core models, run clean migrations, and seed baseline data
**Requirements:** FOUND-01, FOUND-02, FOUND-03, FOUND-04
**Status:** not_started

### Success Criteria
1. `django-admin startproject` + all 5 apps created (organizations, ingestion, normalization, audit, emissions)
2. PostgreSQL connected and `python manage.py migrate` runs cleanly from scratch
3. Organization model with name, slug, created_at fields exists and is admin-registered
4. All 9 core models exist with proper FK relationships: Organization, DataSource, RawUpload, RawRecord, NormalizedEmissionRecord, ReviewStatus, AuditLog, EmissionFactor, UnitConversion
5. `python manage.py makemigrations && migrate` produces zero errors
6. Django admin shows all models

---

## Phase 2: Ingestion Pipelines & Mock Datasets
**Goal:** Build the 3 source-specific ingestion services, create realistic mock datasets, and store raw data (RawUpload + RawRecord) reliably
**Requirements:** SAP-01 – SAP-06, UTIL-01 – UTIL-05, TRVL-01 – TRVL-05, DATA-01 – DATA-05
**Status:** not_started

### Success Criteria
1. SAP CSV with intentionally messy columns (30+ rows, mixed dates, plant codes) exists as mock file
2. Utility electricity CSV with 12-month billing periods, multiple meter IDs, mixed kWh/MWh exists as mock file
3. Corporate travel mock JSON with 20+ records (flights with IATA codes, hotels, ground transport) exists
4. `SAPIngestionService.ingest(file, organization)` creates RawUpload + N RawRecords without crashing on bad rows
5. `UtilityIngestionService.ingest(file, organization)` creates RawUpload + N RawRecords with billing metadata preserved
6. `TravelIngestionService.ingest(mock_data, organization)` creates RawUpload + N RawRecords with travel type mapped
7. A SAP CSV with 2 intentionally malformed rows still processes the remaining valid rows (stored with error_detail on failures)
8. EmissionFactor seed data fixture loaded successfully covers: fuel combustion, electricity, flight (short/medium/long haul), hotel, ground transport
9. Management command `python manage.py seed_data` loads org + emission factors without error

---

## Phase 3: Normalization Engine
**Goal:** Build the normalization engine that transforms RawRecords from all 3 sources into unified NormalizedEmissionRecord with correct CO2e
**Requirements:** NORM-01 – NORM-07
**Status:** not_started

### Success Criteria
1. `NormalizationEngine.normalize(raw_record)` produces a NormalizedEmissionRecord for a valid SAP row
2. `NormalizationEngine.normalize(raw_record)` produces a NormalizedEmissionRecord for a valid utility row
3. `NormalizationEngine.normalize(raw_record)` produces a NormalizedEmissionRecord for each travel type (flight/hotel/ground)
4. `UnitConverter.convert(value, from_unit, to_unit)` correctly converts kWh→MWh and liters→liters (identity)
5. Scope 1/2/3 is assigned from a category→scope lookup table, not from freetext
6. `emission_factor_id` is stored on every NormalizedEmissionRecord (snapshot at calculation time)
7. CO2e = activity_value × emission_factor.value, stored on NormalizedEmissionRecord.co2e
8. A full pipeline test: upload SAP mock CSV → NormalizedEmissionRecord.co2e value matches expected manual calculation

---

## Phase 4: Audit, Validation & Suspicious Row Flagging
**Goal:** Build the audit logging system, row-level validation service, and suspicious row detection
**Requirements:** AUDIT-01 – AUDIT-05, VALID-01 – VALID-05
**Status:** not_started

### Success Criteria
1. AuditLog entry is created automatically when NormalizedEmissionRecord is created (via Django signal)
2. AuditLog entry is created with old_value + new_value when NormalizedEmissionRecord is updated
3. NormalizedEmissionRecord.is_manually_edited becomes True when the record is edited after normalization
4. NormalizedEmissionRecord.status transitions: pending_review → approved works (no crash)
5. Pydantic validation schema per source type rejects rows with missing required fields
6. RawRecord.validation_status = 'failed' + error_detail populated for a row with missing required field
7. Rows with CO2e > 3 standard deviations from batch mean are flagged as suspicious
8. `ValidationService.validate(raw_record)` returns structured error list for invalid rows

---

## Phase 5: REST APIs & Integration Tests
**Goal:** Build all 7 REST API endpoints, wire them to the service layer, and write integration tests that cover the full ingestion pipeline
**Requirements:** API-01 – API-07
**Status:** not_started

### Success Criteria
1. POST /api/ingestion/sap/upload/ accepts multipart CSV and returns upload batch ID
2. POST /api/ingestion/utility/upload/ accepts multipart CSV and returns upload batch ID
3. POST /api/ingestion/travel/trigger/ accepts JSON config and returns job result
4. GET /api/ingestion/uploads/ returns list of RawUpload records for the organization
5. GET /api/emissions/normalized/ returns paginated NormalizedEmissionRecord list (filterable by scope, status, date range)
6. GET /api/ingestion/validation-failures/ returns RawRecords where validation_status=failed
7. GET /api/emissions/suspicious/ returns NormalizedEmissionRecords where is_suspicious=True
8. Integration test: upload SAP mock CSV → assert NormalizedEmissionRecord count increased → assert co2e > 0
9. Integration test: upload utility CSV with 1 bad row → assert RawRecord with validation_status=failed exists → remaining rows normalized successfully

---

## Traceability

| Phase | Requirements Covered | Count |
|-------|---------------------|-------|
| Phase 1 | FOUND-01–04 | 4 |
| Phase 2 | SAP-01–06, UTIL-01–05, TRVL-01–05, DATA-01–05 | 21 |
| Phase 3 | NORM-01–07 | 7 |
| Phase 4 | AUDIT-01–05, VALID-01–05 | 10 |
| Phase 5 | API-01–07 | 7 |
| **Total** | | **49** |

> Note: 49 mapped vs 43 declared — Phase 2 captures DATA requirements inline with ingestion.

---
*Roadmap created: 2026-05-25*
*Milestone: v1.0*
