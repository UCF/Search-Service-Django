import os

from settings import BASE_DIR
from django.utils.log import DEFAULT_LOGGING

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'SUPERSECRETKEYHEREPLEASEANDTHANKYOU'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Set to true for local development with the Angular
LOCAL = False

ALLOWED_HOSTS = []

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME'  : os.path.join(BASE_DIR, 'db.sqlite3'),
    },
    'teledata': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME'  : os.path.join(BASE_DIR, 'teledata.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static") # Comment out when using locally
STATICFILES_DIRS = [
    # Add static root path when debugging locally
]

CORS_ORIGIN_ALLOW_ALL = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        },
        'django.server': DEFAULT_LOGGING['formatters']['django.server'],
        'programs.management.commands': DEFAULT_LOGGING['formatters']['django.server'],
        'teledata.management.commands': DEFAULT_LOGGING['formatters']['django.server'],
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
        'sentry': {
            'level': 'WARNING',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler'
        },
        'django.server': DEFAULT_LOGGING['handlers']['django.server'],
        'programs.management.commands': DEFAULT_LOGGING['handlers']['django.server'],
        'teledata.management.commands': DEFAULT_LOGGING['handlers']['django.server'],
    },
    'loggers': {
        '': {
            'level': 'WARNING',
            'handlers': ['console', 'sentry'],
        },
        'django.server': DEFAULT_LOGGING['loggers']['django.server'],
        'programs.management.commands': DEFAULT_LOGGING['loggers']['django.server'],
        'teledata.management.commands': DEFAULT_LOGGING['loggers']['django.server'],
    }
}

APP_NAME = 'UCF Search Service'

# Set a base CIP version to use when filtering other objects by CIP.
# More info: https://nces.ed.gov/ipeds/cipcode/
CIP_CURRENT_VERSION = '2010'

# Set a base SOC version to use when filtering other objects by SOC.
# More info: https://www.bls.gov/soc/
SOC_CURRENT_VERSION = '2010'

# Set the current employment projection report year range
PROJ_CURRENT_REPORT = '1828'

# The default year + month + day limit of how old imported images can be.
# NOTE: increasing this value could cause older images to be removed
# during a future image import!
IMPORTED_IMAGE_LIMIT = (2017, 12, 1)

# The domain name for UCF's Tandem Vault.
UCF_TANDEMVAULT_DOMAIN = 'ucf.tandemvault.com'

# An API key to use with UCF's Tandem Vault that has admin-level user access.
TANDEMVAULT_ADMIN_API_KEY = ''

# An API key to use with UCF's Tandem Vault that has UCF Communicator-level user access.
TANDEMVAULT_COMMUNICATOR_API_KEY = ''

# An AWS Access Key ID with sufficient permissions to access Rekognition.
AWS_ACCESS_KEY = ''

# An AWS Secret Key for accessing Rekognition.
AWS_SECRET_KEY = ''

# The region name to use when accessing Rekognition.
AWS_REGION = 'us-east-1'

# Conditional outcomes for setting the default program profile
PROGRAM_PROFILE = [
    {
        'conditions': [
            {
                'field': 'online',
                'value': True
            }
        ],
        'value': 'Online'
    },
    {
        'conditions': [],
        'value': 'Main Site'
    }
]
