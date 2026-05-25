# Features Research — ESG Emissions Ingestion Platform

## Table Stakes (Must Have — Users Expect These)

### Multi-Source Ingestion
- CSV file upload endpoint per source type
- REST API trigger for mocked external API sources
- Raw data preservation (never mutate source records)
- Batch/job tracking per ingestion run

### Data Normalization
- Unified emission record schema across all sources
- Scope 1 / 2 / 3 categorization
- Unit normalization (kWh→MWh, liters, km distances)
- Emission factor application → CO2e calculation
- Source type metadata on every record

### Validation & Quality
- Row-level validation (don't crash on bad rows)
- Error storage with original row context
- Suspicious/anomalous row flagging
- Required field presence checks

### Audit & Traceability
- Every normalized record traces to raw source
- All data changes logged with timestamp + actor
- Approval-ready status field (pending → approved/rejected)
- Upload batch traceability

### Multi-Tenancy
- Organization-scoped data isolation
- All models linked to Organization
- API filters by organization

### REST APIs
- Upload endpoints per source
- List/filter endpoints for raw and normalized data
- Validation failure and suspicious row endpoints

## Differentiators (Competitive Advantage — Not Required for v1)

- Analyst review dashboard with workflow approval
- Real authentication (JWT, RBAC per organization)
- Emission factor library management UI
- Historical trend analysis
- Regulatory reporting export (GHG Protocol format)
- Bulk approval/rejection of records
- Real-time ingestion progress (WebSocket)

## Anti-Features (Deliberately NOT Building)

| Feature | Reason |
|---------|--------|
| Frontend dashboard | Section 2 scope |
| Auth complexity | Overengineering for Section 1 |
| Microservices | Complexity without benefit for this scale |
| AI anomaly detection | Future scope |
| Live sync / WebSocket | Not needed for batch ingestion |
| Kubernetes deployment | Section 3 scope |

## Feature Complexity Assessment

| Feature | Complexity | Key Challenge |
|---------|-----------|---------------|
| SAP CSV ingestion | Medium | Inconsistent column names, messy date formats |
| Utility CSV ingestion | Low-Medium | kWh/MWh conversion, billing period parsing |
| Travel API ingestion | Medium | Airport code→distance calculation, multi-category mapping |
| Normalization engine | High | Unit conversion, emission factor lookup, scope mapping |
| Audit logging | Low | Signal-based auto-logging pattern |
| Row validation | Medium | Schema-per-source design, error message quality |
| Multi-tenancy | Low | FK to Organization on all models |

## Dependencies Between Features

```
Organization model → all other models
DataSource config → ingestion services
RawUpload + RawRecord → NormalizedEmissionRecord
EmissionFactor → NormalizedEmissionRecord.co2e
UnitConversion → NormalizedEmissionRecord.normalized_value
NormalizedEmissionRecord → ReviewStatus
AuditLog → all mutation operations
```
