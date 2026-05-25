import logging
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from apps.normalization.models import NormalizedEmissionRecord
from services.audit.service import AuditService

logger = logging.getLogger(__name__)

# Cache old states on the instance before save
@receiver(pre_save, sender=NormalizedEmissionRecord)
def cache_old_state(sender, instance, **kwargs):
    if instance.pk:
        try:
            # Fetch the current DB state before the save overwrites it
            instance._old_state = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            instance._old_state = None
    else:
        instance._old_state = None

# Log changes after save
@receiver(post_save, sender=NormalizedEmissionRecord)
def log_emission_record_change(sender, instance, created, **kwargs):
    action = 'create' if created else 'update'
    
    try:
        AuditService.log_change(
            organization=instance.organization,
            instance=instance,
            action=action,
            actor='system_signal',
            old_instance=getattr(instance, '_old_state', None)
        )
    except Exception as e:
        # Never fail a save because of an audit log error
        logger.error(f"Failed to write audit log for {instance}: {e}")
