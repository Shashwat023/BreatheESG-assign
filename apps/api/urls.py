# API URL router — populated incrementally as endpoints are built
# Phase 2 adds ingestion endpoints, Phase 5 completes all 7 API endpoints

from django.urls import path, include

urlpatterns = [
    # Ingestion endpoints (added in Phase 2 + Phase 5)
    # path('ingestion/', include('apps.api.ingestion_urls')),

    # Emissions endpoints (added in Phase 5)
    # path('emissions/', include('apps.api.emissions_urls')),
]
