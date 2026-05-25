# breatheESG — ESG Emissions Ingestion Platform

## What This Is

breatheESG is a Django REST + React enterprise ESG platform where large organizations upload emissions and activity data from multiple messy real-world enterprise systems (SAP, utility portals, travel management tools). The backend ingests, normalizes, validates, and prepares emissions records for analyst review, mapping all data into a unified Scope 1/2/3 CO2e schema ready for regulatory reporting.

## Core Value

Every emission record — regardless of source — must be traceable back to its raw origin, normalized into a consistent CO2e schema, and auditable end-to-end before an analyst approves it.

## Requirements

### Validated

(None yet — ship to validate)

### Active

<!-- Section 1: Core ingestion + normalization backend -->

- [ ] INGEST-01: System accepts SAP fuel/procurement CSV uploads and stores raw records
- [ ] INGEST-02: System accepts utility electricity CSV portal exports and stores raw records
- [ ] INGEST-03: System can trigger a mocked REST ingestion of corporate travel data (Concur/Navan style)
- [ ] INGEST-04: Raw source data is always preserved verbatim (never overwritten)
- [ ] INGEST-05: Every ingestion is tracked as a batch (upload metadata, timestamps, source type)
- [ ] NORM-01: All ingested records are normalized into a unified NormalizedEmissionRecord schema
- [ ] NORM-02: Normalization maps scope (Scope 1/2/3), category, activity_value, activity_unit, co2e
- [ ] NORM-03: Unit conversion is handled (liters→liters, kWh→MWh, distance calculation for travel)
- [ ] NORM-04: Emission factors are stored and referenced per record
- [ ] NORM-05: Corporate travel records handle flights (airport codes, distance), hotels, ground transport
- [ ] TRACE-01: Every normalized record references its original source, upload batch, and raw row
- [ ] TRACE-02: Records track whether they were manually edited after normalization
- [ ] AUDIT-01: All data changes are logged to an AuditLog model
- [ ] AUDIT-02: Records support an approval-ready status workflow (pending_review → approved/rejected)
- [ ] VALID-01: Invalid/malformed rows do not crash ingestion — they are stored with row-level error details
- [ ] VALID-02: Suspicious rows are flagged (anomalous values, missing required fields)
- [ ] MULTI-01: All records belong to an Organization (multi-tenancy)
- [ ] API-01: REST API to upload SAP CSV
- [ ] API-02: REST API to upload utility electricity CSV
- [ ] API-03: REST API to trigger mocked travel API ingestion
- [ ] API-04: REST API to list raw uploads and normalized records
- [ ] API-05: REST API to fetch validation failures and suspicious rows

### Out of Scope

- Polished React frontend dashboard — Section 2
- Authentication complexity (JWT, OAuth, RBAC) — Section 2
- Production deployment, Docker, Kubernetes — Section 3
- AI/ML features (anomaly detection, predictive emission factors) — future
- WebSocket / live sync — future
- Microservices architecture — deliberate: keep as monolith for clarity

## Context

- **Assignment context:** 3-section assignment; this is Section 1 of 3
- **Section 2** will add the analyst review dashboard (React + DRF)
- **Section 3** will add deployment and documentation
- **Data sources:** SAP CSV exports (messy column names, inconsistent dates, plant codes), utility portal CSVs (billing periods, meter IDs, kWh/MWh), and mocked Concur/Navan travel API (flights, hotels, ground transport)
- **Normalized output schema:** `{organization, source_type, scope, category, activity_value, activity_unit, normalized_value, normalized_unit, emission_factor, co2e, status}`
- **Emission factor database:** Pre-seeded with DEFRA/EPA standard factors per category
- **Design philosophy:** Clean architecture, explainability over cleverness, service-layer pattern, realistic enterprise data handling

## Constraints

- **Tech Stack**: Django + Django REST Framework + PostgreSQL — no framework changes
- **Python**: Service-layer architecture preferred over fat views/models
- **Async**: Celery optional for async ingestion if beneficial — not required
- **Scope**: Backend only for Section 1 — no frontend beyond simple API testing
- **Complexity**: Avoid overengineering; prioritize clean, readable, explainable code
- **No auth complexity**: Simple organization-scoped queries suffice for now

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Django monolith (not microservices) | Explainability + assignment context | — Pending |
| Service-layer architecture | Separates ingestion logic from views/models | — Pending |
| Raw records always preserved | Source traceability requirement | — Pending |
| Celery optional | Not required for demo; add only if pipeline complexity warrants | — Pending |
| PostgreSQL | Relational model suits audit trails + multi-tenancy | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-25 after initialization*
