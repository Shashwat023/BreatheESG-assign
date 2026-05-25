"""
AuditLog — records every data mutation in the system.

Design principle: We log creates, updates, and deletes on NormalizedEmissionRecord.
Each log entry stores old_value + new_value as JSON diffs, so analysts can see
exactly what changed and when.

AuditLog entries are IMMUTABLE — never delete or update them.
They are the legal/compliance record of what data existed and when it changed.

Usage: AuditService.log_change() is called explicitly in service methods,
or via Django signals for automatic coverage on model saves/deletes.
"""
from django.db import models
from apps.organizations.models import Organization


class AuditLog(models.Model):
    """
    Immutable audit trail for all data mutations in the ESG platform.

    Every create, update, approve, and reject operation on emission records
    produces an AuditLog entry. This enables:
    - Regulatory compliance (who changed what and when)
    - Debug capability (trace how a record evolved)
    - Analyst accountability (who approved/rejected)
    """
    ACTION_CHOICES = [
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
        ('flag_suspicious', 'Flagged as Suspicious'),
        ('ingest', 'Ingested'),
    ]

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='audit_logs'
    )

    # Generic reference — we use model_name + object_id rather than ContentType
    # to keep the schema simple and avoid Django ContentType dependency.
    model_name = models.CharField(
        max_length=100,
        help_text="Django model name (e.g., 'NormalizedEmissionRecord', 'RawUpload')"
    )
    object_id = models.IntegerField(
        help_text="Primary key of the affected model instance"
    )

    action = models.CharField(max_length=50, choices=ACTION_CHOICES)

    # JSON snapshot of the record state before and after the change.
    # For 'create': old_value is null, new_value is the created state.
    # For 'update': both fields populated with diff.
    # For 'delete': old_value is the deleted state, new_value is null.
    old_value = models.JSONField(
        null=True, blank=True,
        help_text="State of the record before the change"
    )
    new_value = models.JSONField(
        null=True, blank=True,
        help_text="State of the record after the change"
    )

    # Who triggered the change.
    # 'system' for automated ingestion/normalization.
    # 'api' for API calls without auth (Phase 1).
    # Future: user email or ID when auth is implemented in Phase 2.
    actor = models.CharField(
        max_length=255, default='system',
        help_text="Who triggered this change ('system', 'api', or future: user identifier)"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['organization', 'timestamp']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        return (
            f"{self.action} on {self.model_name}#{self.object_id} "
            f"@ {self.timestamp:%Y-%m-%d %H:%M} by {self.actor}"
        )
