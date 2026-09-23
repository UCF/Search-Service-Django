
# Appended to a copy of settings_local.tmpl.py by the test workflow
# (.github/workflows/tests.yml) to point Django at the job's database.

DATABASES['default'] = {
    'ENGINE': os.environ['DB_ENGINE'],
    'NAME': 'search',
    'USER': os.environ['DB_USER'],
    'PASSWORD': 'ci',
    'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
    'PORT': os.environ['DB_PORT'],
}

if DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
    # A case-insensitive collation, like MySQL's default, so tests see
    # the same text matching production does.
    DATABASES['default']['OPTIONS'] = {'charset': 'utf8mb4'}
    DATABASES['default']['TEST'] = {
        'CHARSET': 'utf8mb4',
        'COLLATION': 'utf8mb4_general_ci',
    }
