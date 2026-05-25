"""
ReviewStatus — tracks the analyst approval workflow for normalized emission records.

Design principle: Status transitions are logged here as history entries,
not as a single mutable status field. This gives analysts full visibility
into the review lifecycle of each record.

The NormalizedEmissionRecord.status field is the source of truth (current status),
while ReviewStatus captures the complete history of transitions.
"""
from django.db import models
from apps.organizations.models import Organization
from apps.normalization.models import NormalizedEmissionRecord


class ReviewStatus(models.Model):
    """
    Records each status transition in the analyst approval workflow.

    One entry per transition (not one mutable record per emission).
    Lets analysts see: "This record was pending → flagged for clarification →
    updated by analyst → approved."

    Status transitions:
    pending_review → approved (analyst accepts record as-is)
    pending_review → rejected (analyst rejects, requires re-ingestion)
    pending_review → needs_clarification (analyst needs more context)
    needs_clarification → approved (after clarification provided)
    needs_clarification → rejected
    """
    STATUS_CHOICES = [
        ('pending_review', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('needs_clarification', 'Needs Clarification'),
    ]

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='review_statuses'
    )
    emission_record = models.ForeignKey(
        NormalizedEmissionRecord, on_delete=models.CASCADE,
        related_name='review_history'
    )
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    previous_status = models.CharField(max_length=50, blank=True)
    reviewer = models.CharField(
        max_length=255, default='system',
        help_text="Who set this status ('system' for auto, future: user identifier)"
    )
    notes = models.TextField(
        blank=True,
        help_text="Reviewer notes, rejection reason, or clarification request"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.emission_record} → {self.status} (by {self.reviewer})"
