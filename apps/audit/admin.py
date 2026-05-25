from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['organization', 'model_name', 'object_id', 'action', 'actor', 'timestamp']
    list_filter = ['action', 'model_name', 'organization']
    # AuditLog is immutable — all fields readonly
    readonly_fields = [
        'organization', 'model_name', 'object_id', 'action',
        'old_value', 'new_value', 'actor', 'timestamp', 'notes'
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
