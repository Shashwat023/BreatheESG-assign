from django.contrib import admin
from .models import ReviewStatus


@admin.register(ReviewStatus)
class ReviewStatusAdmin(admin.ModelAdmin):
    list_display = ['emission_record', 'status', 'previous_status', 'reviewer', 'created_at']
    list_filter = ['status', 'organization']
    readonly_fields = ['created_at']
