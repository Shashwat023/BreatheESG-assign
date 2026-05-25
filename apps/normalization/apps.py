from django.apps import AppConfig


class NormalizationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.normalization'

    def ready(self):
        import apps.normalization.signals  # noqa

    verbose_name = 'Normalization'
