from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.api.views import UploadViewSet, NormalizedRecordViewSet, AuditLogViewSet

router = DefaultRouter()
router.register(r'uploads', UploadViewSet, basename='upload')
router.register(r'records', NormalizedRecordViewSet, basename='record')
router.register(r'audit', AuditLogViewSet, basename='audit')

urlpatterns = [
    path('', include(router.urls)),
]
