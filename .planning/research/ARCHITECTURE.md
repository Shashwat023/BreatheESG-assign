# Architecture Research — breatheESG Backend

## System Architecture Overview

### Component Boundaries

```
┌─────────────────────────────────────────────────────────────┐
│                      Django Application                      │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  organizations│  │   ingestion  │  │   normalization  │  │
│  │   app        │  │    app       │  │      app         │  │
│  │              │  │              │  │                  │  │
│  │ Organization │  │ DataSource   │  │ NormalizedRecord  │  │
│  │              │  │ RawUpload    │  │ EmissionFactor   │  │
│  │              │  │ RawRecord    │  │ UnitConversion   │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │    audit     │  │   emissions  │  │     api          │  │
│  │    app       │  │    app       │  │   (DRF views)    │  │
│  │              │  │              │  │                  │  │
│  │  AuditLog    │  │ ReviewStatus │  │  upload CSVs     │  │
│  │              │  │              │  │  list records    │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Service Layer                           │   │
│  │  SAPIngestionService | UtilityIngestionService       │   │
│  │  TravelIngestionService | NormalizationEngine        │   │
│  │  ValidationService | AuditService | UnitConverter   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │    PostgreSQL      │
                    │    Database       │
                    └───────────────────┘
```

### Data Flow

```
User uploads CSV / triggers API
       │
       ▼
DRF View (API endpoint)
       │
       ▼
Ingestion Service (source-specific)
  ├── Store raw file → RawUpload
  ├── Parse rows → RawRecord (one per source row)
  └── Trigger normalization
       │
       ▼
Normalization Engine
  ├── Validate row (pydantic schema)
  ├── Map columns to standard fields
  ├── Convert units (UnitConverter service)
  ├── Look up EmissionFactor
  ├── Calculate CO2e
  └── Create NormalizedEmissionRecord
       │
       ├── (if error) → mark RawRecord.validation_status=failed
       │                store RawRecord.error_detail
       └── (if suspicious) → flag NormalizedRecord.is_suspicious
       │
       ▼
AuditLog (auto-logged via signals)
       │
       ▼
NormalizedEmissionRecord.status = "pending_review"
```

### Django App Structure

```
breatheESG/
├── manage.py
├── breatheESG/              # project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── organizations/       # Organization model, multi-tenancy
│   ├── ingestion/           # DataSource, RawUpload, RawRecord
│   ├── normalization/       # NormalizedEmissionRecord, EmissionFactor, UnitConversion
│   ├── audit/               # AuditLog
│   ├── emissions/           # ReviewStatus, status workflow
│   └── api/                 # DRF serializers, views, urls
├── services/
│   ├── ingestion/
│   │   ├── sap_ingestion.py
│   │   ├── utility_ingestion.py
│   │   └── travel_ingestion.py
│   ├── normalization/
│   │   ├── normalization_engine.py
│   │   └── unit_converter.py
│   └── audit/
│       └── audit_service.py
├── data/
│   ├── mock_datasets/       # Sample SAP, utility, travel CSVs
│   └── emission_factors/    # Seed data JSON/CSV
└── tests/
```

### Build Order (Dependency Chain)

1. **Organization model** — everything depends on this
2. **Ingestion models** (DataSource, RawUpload, RawRecord) — depend on Organization
3. **Normalization models** (EmissionFactor, UnitConversion, NormalizedEmissionRecord) — depend on RawRecord
4. **Audit models** (AuditLog) — depend on NormalizedEmissionRecord
5. **Emissions models** (ReviewStatus) — depend on NormalizedEmissionRecord
6. **Service layer** — depends on all models
7. **API layer** (DRF views/serializers) — depends on services
8. **Mock datasets + seed data** — depends on models + services

### Integration Points

- DRF views → Ingestion Services (not direct model access)
- Ingestion Services → Normalization Engine (pipeline pattern)
- Normalization Engine → AuditLog (via signals or explicit calls)
- All models → Organization (FK, no cross-org data leakage)

## Suggested Build Order for Phases

1. **Foundation**: Project setup + Organization + DB schema
2. **Ingestion**: RawUpload, RawRecord, source-specific services + mock data
3. **Normalization**: NormalizedEmissionRecord, EmissionFactor, UnitConverter, NormalizationEngine
4. **Audit + Validation**: AuditLog, ReviewStatus, validation service, suspicious row flagging
5. **APIs + Integration**: All DRF endpoints, integration tests, API documentation
