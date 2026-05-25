---
phase: 4
plan: "04-01"
status: complete
completed: 2026-05-25
---

# Summary: 04-01 Audit, Validation & Suspicious Row Flagging

## What was built

Implemented the validation service for detecting anomalous CO2e values and the audit service for tracking all mutations.

- `services/validation/service.py`: Built `ValidationService` which uses Django's `Avg` and `StdDev` aggregations to flag records where CO2e deviates by more than 3 sigma from the batch mean. Also flags negative/zero CO2e and impossible travel distances.
- `services/audit/service.py`: Built `AuditService` which computes minimal JSON diffs between the old and new state of a model using `model_to_dict` and `DjangoJSONEncoder`. Saves the diff to the immutable `AuditLog` table.
- `apps/normalization/signals.py`: Wired `pre_save` and `post_save` signals to `NormalizedEmissionRecord` to automatically call `AuditService.log_change` whenever a record is created or updated, ensuring audit compliance without cluttering business logic.

## Key files created/modified

- `services/validation/__init__.py`
- `services/validation/service.py`
- `services/audit/__init__.py`
- `services/audit/service.py`
- `apps/normalization/signals.py`
- `apps/normalization/apps.py` (modified to load signals)

## Deviations from plan

None. All services implemented as specified.
