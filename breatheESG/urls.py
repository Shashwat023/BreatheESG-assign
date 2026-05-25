"""
URL configuration for breatheESG project.

API endpoints are namespaced under /api/ and implemented in apps/api/.
OpenAPI documentation is available at /api/docs/ (Swagger UI).
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),

    # API endpoints
    path('api/', include('apps.api.urls')),

    # OpenAPI schema + documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
