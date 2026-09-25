
# Appended to a copy of settings_local.tmpl.py to configure it from
# environment variables. The container image (Dockerfile) and the test
# workflow (.github/workflows/tests.yml) both build settings_local.py
# this way.

import os

SECRET_KEY = os.environ['SECRET_KEY']

DEBUG = os.environ.get('DEBUG', '').lower() == 'true'

ALLOWED_HOSTS = [
    host.strip() for host in os.environ.get('ALLOWED_HOSTS', '').split(',') if host.strip()
]

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
