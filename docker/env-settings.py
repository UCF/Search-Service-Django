
# Appended to a copy of settings_local.tmpl.py to configure it from
# environment variables. The container image (Dockerfile) and the test
# workflow (.github/workflows/tests.yml) both build settings_local.py
# this way. Only SECRET_KEY, DB_ENGINE and DB_NAME are required; anything
# else left unset keeps the template's value. Sentry needs no setting
# here: raven reads SENTRY_DSN from the environment itself.

import json
import os


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).lower() == 'true'


SECRET_KEY = os.environ['SECRET_KEY']

DEBUG = env_bool('DEBUG')

ALLOWED_HOSTS = [
    host.strip() for host in os.environ.get('ALLOWED_HOSTS', '').split(',') if host.strip()
]

# In Azure, App Service and Front Door terminate HTTPS and forward the
# request. These make Django use the scheme and host the visitor used.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

# Cache-Control headers for Front Door, from CACHE_CONTROL_TTLS in
# settings.py.
CACHE_CONTROL_ENABLED = True

DATABASES['default'] = {
    'ENGINE': os.environ['DB_ENGINE'],
    'NAME': os.environ['DB_NAME'],
    'USER': os.environ.get('DB_USER', ''),
    'PASSWORD': os.environ.get('DB_PASSWORD', ''),
    'HOST': os.environ.get('DB_HOST', ''),
    'PORT': os.environ.get('DB_PORT', ''),
}

if DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
    # A case-insensitive collation, like MySQL's default, so tests see
    # the same text matching production does.
    DATABASES['default']['OPTIONS'] = {'charset': 'utf8mb4'}
    DATABASES['default']['TEST'] = {
        'CHARSET': 'utf8mb4',
        'COLLATION': 'utf8mb4_general_ci',
    }

# Media uploads stay in S3 until they move to Blob Storage after cutover.
USE_S3 = env_bool('USE_S3')
S3_ENV = os.environ.get('S3_ENV', S3_ENV)

if USE_S3:
    AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
    AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', 'ucf-search-service')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
    PUBLIC_MEDIA_LOCATION = f'{S3_ENV}/media'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{PUBLIC_MEDIA_LOCATION}/'
    DEFAULT_FILE_STORAGE = 'core.storage_backends.PublicMediaStorage'

# Credentials for the services the imports call
GRADUATE_SLATE_ENDPOINTS = {
    'deadlines': {
        'endpoint': os.environ.get('SLATE_DEADLINES_ENDPOINT', ''),
        'username': os.environ.get('SLATE_DEADLINES_USERNAME', ''),
        'password': os.environ.get('SLATE_DEADLINES_PASSWORD', ''),
    },
    'guids': {
        'endpoint': os.environ.get('SLATE_GUIDS_ENDPOINT', ''),
        'username': os.environ.get('SLATE_GUIDS_USERNAME', ''),
        'password': os.environ.get('SLATE_GUIDS_PASSWORD', ''),
    },
}
KUALI_BASE_URL = os.environ.get('KUALI_BASE_URL', KUALI_BASE_URL)
KUALI_API_TOKEN = os.environ.get('KUALI_API_TOKEN', KUALI_API_TOKEN)
ACADEMIC_ANALYTICS_API_KEY = os.environ.get('ACADEMIC_ANALYTICS_API_KEY', ACADEMIC_ANALYTICS_API_KEY)
INSTITUTION_GRID_ID = os.environ.get('INSTITUTION_GRID_ID', INSTITUTION_GRID_ID)

# SAML_CLIENT_SETTINGS is the pysaml2 client configuration as JSON, the
# same dictionary the VMs' settings_local.py defines in Python.
USE_SAML = env_bool('USE_SAML')

if USE_SAML:
    SAML2_AUTH['SAML_CLIENT_SETTINGS'] = json.loads(os.environ['SAML_CLIENT_SETTINGS'])
    SAML2_AUTH['ASSERTION_URL'] = os.environ['SAML_ASSERTION_URL']
