"""
Organization model — the multi-tenancy root.

Every data record in the system belongs to an Organization.
This is enforced via FK on all models. No cross-org data leakage is possible
if all QuerySets are filtered by organization.
"""
from django.db import models


class Organization(models.Model):
    """
    Represents an enterprise client (e.g., "ABC Corp").

    All emission data, uploads, and audit trails are scoped to an organization.
    This is the multi-tenancy boundary — every other model in the system has
    a ForeignKey to Organization.
    """
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
