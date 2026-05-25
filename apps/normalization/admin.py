from django.contrib import admin
from .models import EmissionFactor, UnitConversion, NormalizedEmissionRecord


@admin.register(EmissionFactor)
class EmissionFactorAdmin(admin.ModelAdmin):
    list_display = ['category', 'scope', 'factor_value', 'activity_unit', 'factor_source', 'year', 'is_active']
    list_filter = ['scope', 'factor_source', 'year', 'is_active']
    search_fields = ['category', 'subcategory']


@admin.register(UnitConversion)
class UnitConversionAdmin(admin.ModelAdmin):
    list_display = ['from_unit', 'to_unit', 'conversion_factor', 'notes']
    search_fields = ['from_unit', 'to_unit']


@admin.register(NormalizedEmissionRecord)
class NormalizedEmissionRecordAdmin(admin.ModelAdmin):
    list_display = [
        'organization', 'source_type', 'scope', 'category',
        'activity_value', 'activity_unit', 'co2e', 'status', 'is_suspicious'
    ]
    list_filter = ['status', 'scope', 'source_type', 'is_suspicious', 'is_manually_edited', 'organization']
    search_fields = ['category', 'organization__name']
    readonly_fields = ['created_at', 'updated_at']
