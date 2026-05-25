import pytest
from django.conf import settings

def pytest_configure():
    # Override settings to use a fast, local in-memory SQLite database for testing
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
