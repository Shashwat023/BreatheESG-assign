"""
Audit Service.

Provides a unified interface for recording immutable audit logs.
Calculates JSON diffs for model state changes.
"""
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict
from apps.audit.models import AuditLog
from apps.organizations.models import Organization
import json

class AuditService:
    @staticmethod
    def _serialize_model(instance) -> dict:
        """Convert a model instance to a JSON-serializable dict."""
        if not instance:
            return None
        # Using model_to_dict, but excluding related object instances
        data = model_to_dict(instance)
        # Convert Decimals/Dates to strings for JSON
        return json.loads(json.dumps(data, cls=DjangoJSONEncoder))

    @staticmethod
    def log_change(
        organization: Organization,
        instance,
        action: str,
        actor: str = 'system',
        notes: str = '',
        old_instance=None
    ) -> AuditLog:
        """
        Record a state change in the AuditLog.
        
        Args:
            organization: The tenant
            instance: The modified Django model instance
            action: 'create', 'update', 'delete', 'approve', etc.
            actor: Who made the change
            notes: Optional reason
            old_instance: The instance state BEFORE the change
        """
        new_value = AuditService._serialize_model(instance) if action != 'delete' else None
        old_value = AuditService._serialize_model(old_instance) if old_instance else None
        
        # If it's an update, calculate a minimal diff
        if action == 'update' and old_value and new_value:
            diff_old = {}
            diff_new = {}
            for key, val in new_value.items():
                if old_value.get(key) != val:
                    diff_old[key] = old_value.get(key)
                    diff_new[key] = val
            old_value = diff_old
            new_value = diff_new
            
            # Don't log if nothing actually changed
            if not diff_new:
                return None

        return AuditLog.objects.create(
            organization=organization,
            model_name=instance.__class__.__name__,
            object_id=instance.pk,
            action=action,
            actor=actor,
            old_value=old_value,
            new_value=new_value,
            notes=notes
        )
