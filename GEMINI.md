<!-- GSD:project-start source:PROJECT.md -->
## Project

**breatheESG — ESG Emissions Ingestion Platform**

breatheESG is a Django REST + React enterprise ESG platform where large organizations upload emissions and activity data from multiple messy real-world enterprise systems (SAP, utility portals, travel management tools). The backend ingests, normalizes, validates, and prepares emissions records for analyst review, mapping all data into a unified Scope 1/2/3 CO2e schema ready for regulatory reporting.

**Core Value:** Every emission record — regardless of source — must be traceable back to its raw origin, normalized into a consistent CO2e schema, and auditable end-to-end before an analyst approves it.

### Constraints

- **Tech Stack**: Django + Django REST Framework + PostgreSQL — no framework changes
- **Python**: Service-layer architecture preferred over fat views/models
- **Async**: Celery optional for async ingestion if beneficial — not required
- **Scope**: Backend only for Section 1 — no frontend beyond simple API testing
- **Complexity**: Avoid overengineering; prioritize clean, readable, explainable code
- **No auth complexity**: Simple organization-scoped queries suffice for now
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

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
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
