"""
Django settings for breatheESG ESG Emissions Ingestion Platform.

Configuration uses python-decouple for environment variable management.
All sensitive values (DB credentials, SECRET_KEY) come from .env file.

See .env.example for required environment variables.
"""
from pathlib import Path
from decouple import config, Csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ===========================================================================
# SECURITY
# ===========================================================================

SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# ===========================================================================
# APPLICATIONS
# ===========================================================================

INSTALLED_APPS = [
    # Django built-ins
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'django_filters',
    'drf_spectacular',

    # Local apps — ESG platform
    'apps.organizations.apps.OrganizationsConfig',
    'apps.ingestion.apps.IngestionConfig',
    'apps.normalization.apps.NormalizationConfig',
    'apps.audit.apps.AuditConfig',
    'apps.emissions.apps.EmissionsConfig',
    'apps.api.apps.ApiConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'breatheESG.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'breatheESG.wsgi.application'

# ===========================================================================
# DATABASE — PostgreSQL
# Required: DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT in .env
# ===========================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='breathe_esg'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# ===========================================================================
# PASSWORD VALIDATION
# ===========================================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ===========================================================================
# INTERNATIONALIZATION
# ===========================================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ===========================================================================
# STATIC FILES
# ===========================================================================

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ===========================================================================
# DJANGO REST FRAMEWORK
# ===========================================================================

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# ===========================================================================
# DRF SPECTACULAR — OpenAPI schema generation
# ===========================================================================

SPECTACULAR_SETTINGS = {
    'TITLE': 'breatheESG API',
    'DESCRIPTION': (
        'ESG Emissions Ingestion Platform — Section 1 Backend. '
        'Handles multi-source ingestion (SAP, Utility, Travel), normalization, '
        'audit logging, and Scope 1/2/3 CO2e calculation.'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# ===========================================================================
# FILE UPLOAD
# ===========================================================================

# Max upload size for CSVs: 50MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800

# Directory for storing uploaded raw files
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'
