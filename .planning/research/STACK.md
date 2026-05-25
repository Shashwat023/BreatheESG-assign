# Stack Research — breatheESG Backend

## Recommended Stack (2025)

### Core Framework
| Component | Choice | Version | Rationale |
|-----------|--------|---------|-----------|
| Web framework | Django | 5.1.x | Mature ORM, admin, ecosystem; ideal for data-heavy backends |
| API layer | Django REST Framework | 3.15.x | Industry standard for Django APIs |
| Database | PostgreSQL | 16.x | ACID compliance, JSONB for raw data, partitioning for scale |
| Task queue | Celery + Redis | 5.4.x + 7.x | Async ingestion pipelines; optional but recommended for large CSVs |

### Data Ingestion
| Component | Choice | Rationale |
|-----------|--------|-----------|
| CSV parsing | pandas + Python csv module | pandas for complex SAP/utility CSVs; fallback to stdlib for simplicity |
| Data validation | pydantic v2 | Row-level validation schemas; fast, explicit error messages |
| Unit conversion | custom service + pint | pint library handles unit math reliably |

### Supporting Libraries
| Library | Purpose |
|---------|---------|
| django-filter | Filter querysets in list APIs |
| drf-spectacular | OpenAPI schema generation |
| python-dateutil | Parse messy SAP date formats |
| factory_boy | Test data generation |
| pytest-django | Django test runner |

### What NOT to Use
- **SQLite** — insufficient for multi-tenancy + audit trail volumes
- **MongoDB** — loses ACID guarantees needed for financial/ESG data
- **FastAPI** — assignment specifies Django; mismatched
- **Microservices** — over-engineered for this scope; monolith is correct choice
- **Spark/Hadoop** — wildly over-scaled for enterprise CSV volumes

## Confidence Levels

| Component | Confidence | Notes |
|-----------|-----------|-------|
| Django + DRF | ✅ High | Industry standard for this use case |
| PostgreSQL | ✅ High | Clear winner for audit + multi-tenancy |
| pandas for CSV | ✅ High | Handles messy enterprise exports well |
| pydantic v2 | ✅ High | Best-in-class validation |
| Celery | ⚡ Medium | Optional — only add if CSV batches > 10MB |
| pint | ⚡ Medium | Good library; custom service acceptable alternative |
