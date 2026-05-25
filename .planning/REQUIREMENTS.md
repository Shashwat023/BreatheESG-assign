# Requirements: breatheESG — Section 1 Backend

**Defined:** 2026-05-25
**Core Value:** Every emission record — regardless of source — must be traceable back to its raw origin, normalized into a consistent CO2e schema, and auditable end-to-end before an analyst approves it.

## v1 Requirements

Requirements for Section 1: Core Ingestion + Normalization Backend.

### Project Foundation

- [ ] **FOUND-01**: Django project is structured with separate apps (organizations, ingestion, normalization, audit, emissions)
- [ ] **FOUND-02**: PostgreSQL database is configured with proper settings
- [ ] **FOUND-03**: All models can be migrated cleanly from scratch
- [ ] **FOUND-04**: Organization model exists as the multi-tenancy root (all records belong to an Organization)

### Ingestion — SAP Source

- [ ] **SAP-01**: System accepts SAP fuel/procurement CSV upload via REST API endpoint
- [ ] **SAP-02**: Raw SAP file is stored verbatim as a RawUpload record before any processing
- [ ] **SAP-03**: Each CSV row is parsed into a RawRecord with source metadata preserved
- [ ] **SAP-04**: SAP column name inconsistencies are handled via configurable column mapping
- [ ] **SAP-05**: Inconsistent SAP date formats are parsed and normalized (not silently coerced)
- [ ] **SAP-06**: Invalid/malformed SAP rows do not abort the batch — they are stored with error detail

### Ingestion — Utility Electricity Source

- [ ] **UTIL-01**: System accepts utility electricity CSV upload via REST API endpoint
- [ ] **UTIL-02**: Raw utility file is stored verbatim as a RawUpload record
- [ ] **UTIL-03**: Each CSV row is parsed into a RawRecord with billing period and meter ID
- [ ] **UTIL-04**: kWh/MWh unit differences are handled during ingestion
- [ ] **UTIL-05**: Invalid/malformed utility rows do not abort the batch

### Ingestion — Corporate Travel Source

- [ ] **TRVL-01**: System exposes a REST API endpoint to trigger mocked corporate travel data ingestion
- [ ] **TRVL-02**: Mocked travel data simulates Concur/Navan-style records (flights, hotels, ground transport)
- [ ] **TRVL-03**: Flight records include airport codes and distance calculation (or estimation)
- [ ] **TRVL-04**: Different travel types map to different emission categories
- [ ] **TRVL-05**: Travel ingestion creates RawRecords with travel-specific metadata

### Normalization

- [ ] **NORM-01**: All ingested records from all 3 sources are normalized into NormalizedEmissionRecord
- [ ] **NORM-02**: Normalized record contains: organization, source_type, scope, category, activity_value, activity_unit, normalized_value, normalized_unit, emission_factor, co2e, status
- [ ] **NORM-03**: Scope 1/2/3 is assigned systematically from a category→scope mapping (not freetext)
- [ ] **NORM-04**: Unit conversion is centralized in a UnitConverter service
- [ ] **NORM-05**: EmissionFactor table is seeded with DEFRA/EPA standard factors per category
- [ ] **NORM-06**: CO2e is calculated as activity_value × emission_factor and stored on the record
- [ ] **NORM-07**: The specific emission_factor_id used at calculation time is stored on the record (snapshot)

### Audit & Traceability

- [ ] **AUDIT-01**: Every NormalizedEmissionRecord references its RawRecord, RawUpload, and source DataSource
- [ ] **AUDIT-02**: AuditLog records all data mutations (create, update, delete) with timestamp
- [ ] **AUDIT-03**: AuditLog stores old_value and new_value for updates
- [ ] **AUDIT-04**: NormalizedEmissionRecord tracks whether it was manually edited after normalization
- [ ] **AUDIT-05**: NormalizedEmissionRecord has a status field supporting approval workflow states (pending_review → approved / rejected)

### Validation

- [ ] **VALID-01**: Each source has a validation schema (pydantic) that checks required fields and types
- [ ] **VALID-02**: RawRecord stores validation_status (valid / failed / suspicious) and error_detail
- [ ] **VALID-03**: Suspicious rows are flagged on NormalizedEmissionRecord.is_suspicious (e.g., anomalous CO2e values)
- [ ] **VALID-04**: A REST API endpoint returns all validation failures for a given upload batch
- [ ] **VALID-05**: A REST API endpoint returns all suspicious rows across an organization

### REST APIs

- [ ] **API-01**: POST /api/ingestion/sap/upload/ — upload SAP CSV
- [ ] **API-02**: POST /api/ingestion/utility/upload/ — upload utility electricity CSV
- [ ] **API-03**: POST /api/ingestion/travel/trigger/ — trigger mocked travel data ingestion
- [ ] **API-04**: GET /api/ingestion/uploads/ — list raw upload batches
- [ ] **API-05**: GET /api/emissions/normalized/ — list normalized emission records (filterable)
- [ ] **API-06**: GET /api/ingestion/validation-failures/ — list rows with validation errors
- [ ] **API-07**: GET /api/emissions/suspicious/ — list flagged suspicious rows

### Mock Data & Seed Data

- [ ] **DATA-01**: Realistic SAP CSV mock dataset (50+ rows, messy columns, mixed dates, multiple plant codes)
- [ ] **DATA-02**: Realistic utility electricity CSV mock dataset (12 months, multiple meter IDs, kWh+MWh mix)
- [ ] **DATA-03**: Realistic corporate travel mock JSON dataset (flights, hotels, ground transport)
- [ ] **DATA-04**: EmissionFactor seed data covering fuel combustion, electricity, flights, hotels, ground transport
- [ ] **DATA-05**: Management command or fixture to load seed emission factors and sample organizations

## v2 Requirements

### Analyst Dashboard
- **DASH-01**: Analyst can view and approve/reject normalized emission records (Section 2)
- **DASH-02**: Dashboard shows summary statistics per organization (Section 2)

### Authentication
- **AUTH-01**: JWT-based authentication per organization (Section 2)
- **AUTH-02**: Role-based access control (analyst vs admin) (Section 2)

### Deployment
- **DEPLOY-01**: Docker + docker-compose for local development (Section 3)
- **DEPLOY-02**: Production deployment documentation (Section 3)

## Out of Scope

| Feature | Reason |
|---------|--------|
| React frontend / analyst dashboard | Section 2 scope |
| JWT / OAuth authentication | Section 2 scope — adds complexity without benefit for Section 1 |
| Real-time WebSocket updates | Future; batch ingestion doesn't need it |
| AI/ML anomaly detection | Future scope |
| Kubernetes / production deployment | Section 3 scope |
| Microservices architecture | Deliberate: monolith is cleaner and more explainable |
| Email notifications | Future scope |
| Bulk export (PDF/Excel reports) | Future scope |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FOUND-01–04 | Phase 1 | Pending |
| SAP-01–06 | Phase 2 | Pending |
| UTIL-01–05 | Phase 2 | Pending |
| TRVL-01–05 | Phase 2 | Pending |
| NORM-01–07 | Phase 3 | Pending |
| AUDIT-01–05 | Phase 4 | Pending |
| VALID-01–05 | Phase 4 | Pending |
| API-01–07 | Phase 5 | Pending |
| DATA-01–05 | Phase 2 + 3 | Pending |

**Coverage:**
- v1 requirements: 43 total
- Mapped to phases: 43
- Unmapped: 0 ✓

---
*Requirements defined: 2026-05-25*
*Last updated: 2026-05-25 after initial definition*
