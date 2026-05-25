# Phase 1: Project Foundation & Data Architecture - Context

**Gathered:** 2026-05-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Set up the complete Django project structure with all 5 apps (organizations, ingestion, normalization, audit, emissions), configure PostgreSQL, define all 9 core models with proper FK relationships, and run clean migrations. This phase establishes the foundation that all other phases build on.

</domain>

<decisions>
## Implementation Decisions

### the Agent's Discretion
All implementation choices are at the agent's discretion — pure infrastructure phase.

Key constraints from PROJECT.md and REQUIREMENTS.md:
- Django 5.x + DRF 3.15.x + PostgreSQL
- All models must belong to Organization (multi-tenancy from day 1)
- 9 required models: Organization, DataSource, RawUpload, RawRecord, NormalizedEmissionRecord, ReviewStatus, AuditLog, EmissionFactor, UnitConversion
- Service-layer architecture preferred (services/ directory alongside apps/)
- Clean project structure: breatheESG/ (settings), apps/ (5 Django apps), services/, data/, tests/
- requirements.txt with pinned versions
- `python manage.py migrate` must run from scratch with zero errors

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- None yet — greenfield project

### Established Patterns
- Django monolith (not microservices)
- Service-layer architecture (views → services → models)
- Organization FK on all models for multi-tenancy

### Integration Points
- All apps will share Organization model from organizations app
- RawRecord will FK to RawUpload, DataSource
- NormalizedEmissionRecord will FK to RawRecord, EmissionFactor
- AuditLog will FK to NormalizedEmissionRecord

</code_context>

<specifics>
## Specific Ideas

- Project root: breatheESG/ (Django project dir)
- Apps dir: apps/organizations, apps/ingestion, apps/normalization, apps/audit, apps/emissions
- Services dir: services/ingestion/, services/normalization/, services/audit/
- Data dir: data/mock_datasets/, data/emission_factors/
- Tests dir: tests/
- Use `INSTALLED_APPS` with dotted paths: 'apps.organizations', etc.
- requirements.txt with at minimum: Django, djangorestframework, psycopg2-binary, pandas, pydantic, python-dateutil

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>
