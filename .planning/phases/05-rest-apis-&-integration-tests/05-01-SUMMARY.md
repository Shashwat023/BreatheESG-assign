---
phase: 5
plan: "05-01"
status: complete
completed: 2026-05-25
---

# Summary: 05-01 REST APIs

## What was built

Implemented the REST APIs required by the Section 2 frontend using Django REST Framework.

- `apps/api/serializers.py`: Created model serializers for all core entities. Crucially, the `NormalizedEmissionRecordSerializer` includes read-only fields for `raw_data` and `error_detail` from the nested `RawRecord`, ensuring the frontend can show the full source traceability in the review panel without making secondary API calls.
- `apps/api/views.py`: Built DRF `ReadOnlyModelViewSet` for Uploads and AuditLogs (which are immutable), and a full `ModelViewSet` for NormalizedRecords.
- Added a `@action(detail=True, methods=['post'])` for `review` on `NormalizedRecordViewSet`. This action takes `status` and `notes`, creates a `ReviewStatus` history entry, and updates the record (triggering the AuditLog signal automatically).
- `apps/api/urls.py`: Wired all viewsets via DRF `DefaultRouter` to the `/api/` path.

## Key files created/modified

- `apps/api/serializers.py`
- `apps/api/views.py`
- `apps/api/urls.py`

## Deviations from plan

None. The API is ready for the React frontend to consume.
