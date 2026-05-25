# Research Summary — breatheESG Backend (Section 1)

## Key Findings

**Stack:** Django 5.1 + DRF 3.15 + PostgreSQL 16 + pandas for CSV parsing + pydantic v2 for validation + python-dateutil for SAP date handling. Celery optional.

**Table Stakes:** Multi-source ingestion (3 types), raw data preservation, normalization to unified CO2e schema, Scope 1/2/3 mapping, audit logging, row-level validation (no crash on bad rows), multi-tenancy via Organization FK, REST APIs for all operations.

**Watch Out For:**
1. 🔴 Never mutate raw records — always separate RawRecord from NormalizedEmissionRecord
2. 🔴 Filter all API queries by organization — cross-org data leakage is easy to miss
3. 🔴 Wrap per-row normalization in try/except — one bad SAP row must not abort a 10k-row batch
4. 🟡 Store the emission_factor_id used at CO2e calculation time (snapshot pattern)
5. 🟡 Centralize unit conversion in a single service — prevent conversion drift
6. 🟠 SAP exports have chaotic column names — use JSON column mapping config in DataSource

## Recommended Build Order

1. **Phase 1 — Foundation**: Project structure, Organization model, DB schema, settings
2. **Phase 2 — Ingestion**: DataSource + RawUpload + RawRecord models, 3 ingestion services, mock datasets
3. **Phase 3 — Normalization**: EmissionFactor, UnitConversion, NormalizedEmissionRecord, NormalizationEngine
4. **Phase 4 — Audit + Validation**: AuditLog, ReviewStatus, ValidationService, suspicious row flagging
5. **Phase 5 — APIs**: All DRF endpoints, serializers, integration tests

## Architecture Decision: Service Layer

All business logic lives in `services/` — views only call service methods. This:
- Makes logic testable independently of HTTP layer
- Makes pipeline easy to extend (e.g., add Celery without changing views)
- Matches the "explainability" requirement

## Emission Factor Strategy

Seed the EmissionFactor table from DEFRA 2023/EPA GHG factors:
- Fuel combustion (SAP): DEFRA factors per fuel type in kg CO2e/liter
- Electricity (utility): grid emission factor per kWh, region-specific
- Travel (flights): DEFRA/BEIS factors per passenger-km by cabin class
- Travel (hotels): per night CO2e estimate
- Travel (ground transport): per km CO2e by transport mode

## Files Created

- `.planning/research/STACK.md` — library recommendations with confidence levels
- `.planning/research/FEATURES.md` — table stakes vs differentiators vs anti-features
- `.planning/research/ARCHITECTURE.md` — component boundaries, data flow, build order
- `.planning/research/PITFALLS.md` — 12 pitfalls with prevention strategies
