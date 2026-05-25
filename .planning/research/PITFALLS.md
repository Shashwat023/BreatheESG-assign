# Pitfalls Research — ESG Emissions Ingestion Platform

## Critical Pitfalls

### 1. Raw Data Mutation
**Warning signs:** Normalization service updates fields in-place on raw records; no separate raw store
**Prevention:** Always create separate RawRecord (verbatim source) and NormalizedEmissionRecord (processed); never modify raw records after creation
**Phase:** Phase 1 (Foundation) — get this right from the start

### 2. Ingestion Crashing on Bad Rows
**Warning signs:** CSV parsing inside a single transaction; one bad row rolls back entire batch
**Prevention:** Wrap per-row normalization in try/except; store failures in RawRecord.error_detail; continue processing remaining rows
**Phase:** Phase 2 (Ingestion)

### 3. Unit Conversion Inconsistency
**Warning signs:** Hardcoded conversion factors in multiple places; kWh vs MWh confusion; liters vs gallons
**Prevention:** Centralize all unit conversion in a single UnitConverter service; seed UnitConversion table with canonical factors; validate input units at ingestion boundary
**Phase:** Phase 3 (Normalization)

### 4. Emission Factor Ambiguity
**Warning signs:** Single emission factor per category regardless of region/year; CO2e values drift between runs
**Prevention:** EmissionFactor model includes source, year, region, GWP version; NormalizedEmissionRecord stores the exact factor_id used at calculation time (snapshot)
**Phase:** Phase 3 (Normalization)

### 5. Audit Log Gaps
**Warning signs:** Only logging CREATE; missing UPDATE and DELETE; no actor tracking
**Prevention:** Django signals on all mutation operations; log old_value + new_value for updates; include organization_id in every log entry
**Phase:** Phase 4 (Audit)

### 6. Multi-Tenancy Data Leakage
**Warning signs:** API views with `Model.objects.all()` without organization filter; shared emission factor cache
**Prevention:** Override get_queryset() in all ViewSets to filter by organization; write tests that verify cross-org isolation
**Phase:** Phase 1 (Foundation) — enforce from the start

### 7. SAP Column Name Chaos
**Warning signs:** Hardcoded column names in ingestion code; breaks when SAP export format changes
**Prevention:** Column mapping config in DataSource model (JSON field); ingestion service does `df.rename(columns=mapping)` before processing; log unmapped columns as warnings
**Phase:** Phase 2 (Ingestion)

### 8. Date Format Hell
**Warning signs:** dateutil.parser throwing exceptions on SAP dates like "2024.03.15", "15/03/24", "Mar 15 2024"
**Prevention:** Use `dateutil.parser.parse()` with fallback strategies; store parse failures in error_detail; never silently coerce to wrong date
**Phase:** Phase 2 (Ingestion)

### 9. Travel Distance Calculation Complexity
**Warning signs:** Reinventing great-circle distance calculation; missing IATA airport codes database
**Prevention:** Use geopy or haversine library; seed airport code → lat/lon lookup table; fallback to estimated distance by flight duration category (short/medium/long haul)
**Phase:** Phase 2 (Ingestion — travel source)

### 10. API Layer Fat Views
**Warning signs:** Ingestion logic, validation, normalization, audit all happening inside DRF view methods
**Prevention:** Views only call service methods; all business logic in services/; each service has a single responsibility
**Phase:** Phase 5 (APIs)

### 11. Missing Scope Mapping
**Warning signs:** Scope 1/2/3 assigned at record level with no systematic categorization; inconsistent across sources
**Prevention:** Scope mapping table (category → scope) seeded from GHG Protocol; every NormalizedRecord gets scope from this table, not from free-text
**Phase:** Phase 3 (Normalization)

### 12. No Integration Tests
**Warning signs:** All tests are unit tests on individual functions; nobody tests the full pipeline CSV → normalized record
**Prevention:** Integration test per source type that uploads sample CSV → asserts NormalizedEmissionRecord created with correct CO2e value
**Phase:** Each phase — test the full pipeline

## Prevention Strategies Summary

| Risk Level | Area | Prevention |
|------------|------|-----------|
| 🔴 Critical | Raw data mutation | Separate models, never update RawRecord |
| 🔴 Critical | Multi-tenancy leakage | filter_by_org in all viewsets, tested |
| 🔴 Critical | Crash on bad rows | Per-row try/except, error stored |
| 🟡 High | Unit conversion | Centralized UnitConverter service |
| 🟡 High | Emission factor snapshot | Store factor_id used at calculation time |
| 🟡 High | Audit gaps | Signals on all mutations |
| 🟠 Medium | SAP column chaos | JSON column mapping config |
| 🟠 Medium | Date format hell | dateutil with fallbacks |
| 🟠 Medium | Travel distance | geopy + seeded airport table |
| 🟢 Low | Fat views | Service layer architecture |
