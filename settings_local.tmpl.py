import os

from settings import BASE_DIR
from django.utils.log import DEFAULT_LOGGING

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'SUPERSECRETKEYHEREPLEASEANDTHANKYOU'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Set to true for local development with the Angular app
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

# The available CIP versions that can be used.
# More info: https://nces.ed.gov/ipeds/cipcode/
CIP_AVAILABLE_VERSIONS = [
    ('2010', '2010'),
    ('2020', '2020'),
]

# Set a base CIP version to use when filtering other objects by CIP.
# More info: https://nces.ed.gov/ipeds/cipcode/
CIP_CURRENT_VERSION = '2010'

# The available SOC versions that can be used.
# More info: https://www.bls.gov/soc/
SOC_AVAILABLE_VERSIONS = [
    ('2010', '2010'),
    ('2018', '2018'),
]

# Set a base SOC version to use when filtering other objects by SOC.
# More info: https://www.bls.gov/soc/
SOC_CURRENT_VERSION = '2010'

# Available employment project report year ranges
PROJ_AVAILABLE_REPORTS = [
    ('1828', '2018-2028'),
]

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

# The URL to the News API
UCF_NEWS_API = 'https://www.ucf.edu'

# The URL to the Events System API
UCF_EVENTS_API = 'https://events.ucf.edu'

# The URL to the Search Service API
UCF_SEARCH_SERVICE_API = 'https://search.cm.ucf.edu'

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

# Default program application deadline data to load during the
# application deadline importer against all programs (by career, level):
PROGRAM_APPLICATION_DEADLINES = [
    {
        'career': 'Undergraduate',
        'level': ['Bachelors'],
        'deadline_type': 'Domestic',
        'admission_term': 'Fall',
        'display': 'May 1'
    },
    {
        'career': 'Undergraduate',
        'level': ['Bachelors'],
        'deadline_type': 'Domestic',
        'admission_term': 'Spring',
        'display': 'November 1'
    },
    {
        'career': 'Undergraduate',
        'level': ['Bachelors'],
        'deadline_type': 'Domestic',
        'admission_term': 'Summer',
        'display': 'March 1'
    },
    {
        'career': 'Undergraduate',
        'level': ['Bachelors'],
        'deadline_type': 'Transfer',
        'admission_term': 'Fall',
        'display': 'July 1',
    },
    {
        'career': 'Undergraduate',
        'level': ['Bachelors'],
        'deadline_type': 'Transfer',
        'admission_term': 'Spring',
        'display': 'November 1'
    },
    {
        'career': 'Undergraduate',
        'level': ['Bachelors'],
        'deadline_type': 'Transfer',
        'admission_term': 'Summer',
        'display': 'March 1'
    },
    {
        'career': 'Undergraduate',
        'level': ['Bachelors'],
        'deadline_type': 'International',
        'admission_term': 'Fall',
        'display': 'March 1'
    },
    {
        'career': 'Undergraduate',
        'level': ['Bachelors'],
        'deadline_type': 'International',
        'admission_term': 'Spring',
        'display': 'September 1'
    },
    {
        'career': 'Undergraduate',
        'level': ['Bachelors'],
        'deadline_type': 'International',
        'admission_term': 'Summer',
        'display': 'January 1'
    }
]

# Endpoints and credentials for accessing data from
# Graduate Studies' Slate instance
GRADUATE_SLATE_ENDPOINTS = {
    'deadlines': {
        'endpoint': '',
        'username': '',
        'password': ''
    },
    'guids': {
        'endpoint': '',
        'username': '',
        'password': ''
    }
}

# The base URL to use when building catalog URLs during the catalog import
CATALOG_URL_BASE = 'https://catalog.ucf.edu'

# The base URL of the Acalog API
CATALOG_API_BASE = ''

# The API key used to connect to Acalog
CATALOG_API_KEY = ''

# The ID of the current active undergraduate catalog in Acalog
CATALOG_UNDERGRADUATE_ID = 18

# The ID of the current active graduate catalog in Acalog
CATALOG_GRADUATE_ID = 17

# ORCID API Settings
ORCID_BASE_API_URL = 'https://pub.orcid.org/v2.1/'

INSTITUTION_GRID_ID = ''

RESEARCH_MAX_THREADS = 10

# Full name replacements to be performed on college, department and
# organization names for Units generated via map-units.py.
# Full name replacements are case-sensitive. Replacements are performed
# *before* names are Capital Cased.
UNIT_NAME_FULL_REPLACEMENTS = {
    'Amateur Radio Club-K4UCF': ['AMATEUR RADIO CLUB-K4UCF'],
    'Barnes and Noble Bookstore @ UCF': ['BARNES & NOBLE BOOKSTORE@ UCF'],
    'Burnett School of Biomedical Sciences': ['Biomedical Sciences', 'BIOMEDICAL SCIENCES, BURNETT SCHOOL OF'],
    'Center for Advanced Transportation Systems Simulation (CATSS)': ['Ctr. for Advanced Transportation Sys. Simulation', 'CATSS'],
    'Civil, Environmental, and Construction Engineering': ['Civil, Environ, & Constr Engr'],
    'College of Business': ['BUSINESS ADMINISTRATION, COLLEGE OF', 'College of Business Administration'],
    'College of Optics and Photonics': ['CREOL, THE COLLEGE OF OPTICS AND PHOTONICS', 'CREOL'],
    'Counselor Education and School Psychology': ['Counslr Educ & Schl Psychology'],
    'Dean\'s Office': ['Office of the Dean'],
    'Department of Finance, Dr. P. Phillips School of Real Estate': ['DEPARTMENT OF FINANCE/DR. P. PHILLIPS SCHOOL OF REAL ESTATE'],
    'Florida Interactive Entertainment Academy (FIEA)': ['Florida Interactive Entertainment Academy'],
    'Finance': ['Budget & Finance'],
    'Food Service and Lodging Management': ['Food Svcs & Lodging Management'],
    'Industrial Engineering and Management Systems': ['Industrial Engr & Mgmt Sys'],
    'Interdisciplinary Studies': ['Office of Interdisc Studies'],
    'Judaic Studies': ['JUDAIC STUDIES PROGRAM'],
    'Learning Institute for Elders (LIFE @ UCF)': ['LIFE', 'LEARNING INSTITUTE FOR ELDERS  (LIFE @ UCF)'],
    'Modern Languages and Literatures': ['Modern Languages', 'Modern Language & Literatures'],
    'National Center for Optics and Photonics Education, Waco, TX': ['OP-TEC Nat. Ctr.,Optics & Photonics Ed./Waco,TX'],
    'School of Communication Sciences and Disorders': ['Communication Sciences & Disorders Department'],
    'School of Kinesiology and Physical Therapy': ['Kinesiology&Phys Thpy, Schl of'],
    'School of Politics, Security, and International Affairs': ['Pol, Scty & Intl Afrs, Schl of'],
    'School of Teacher Education': ['Teacher Education 2, School'],
    'Tourism, Events and Attractions': ['Tourism Event and Attractions', 'Tourism, Events and Attraction', 'Tourism, Events, and Attractions'],
    'UCF Card Office': ['UCF CARD', 'UCF Card'],
    'UCF Connect - Administration': ['Administration - UCF Connect'],
    'Women\'s Studies': ['Womens Studies', 'WOMEN\'S STUDIES PROGRAM', 'Women\'s Studies Program']
}

# Partial/substring name replacements to be performed on college, department
# and organization names for Units generated via map-units.py.
# Basic replacements are case-sensitive. Replacements are performed *after*
# names are Capital Cased.
UNIT_NAME_PARTIAL_REPLACEMENTS = {
    '\'': ['’'],
    'Academic': ['Acad.'],
    'Additional': ['Add.'],
    'Administration': ['Adm.', 'Admin.'],
    ' and ': [' & '],
    'Application': ['App.'],
    'AVP': ['Avp'],
    'Business ': ['Bus '],
    'Café': ['Cafe'],
    'Center': ['Ctr.'],
    'Children': ['Childern'],
    'Communication ': ['Comm '],
    'Counselor': ['Counslr'],
    'Department': ['Dept'],
    'Demonstration': ['Demo.'],
    'Educational ': ['Educ. ', 'Educ ', 'Ed '],
    'Engineering': ['Engr'],
    'Florida': ['Fla.'],
    'General': ['Gen.'],
    'Graduate ': ['Grad '],
    'Information': ['Inform.'],
    'Institute': ['Inst.'],
    'International': ['Intl'],
    'Leadership': ['Ldrshp'],
    'Management': ['Mgmt.', 'Mgmt'],
    'NanoScience': ['Nanoscience'],
    'Office': ['Ofc.'],
    'Programs': ['Prgms'],
    'Regional': ['Rgnl'],
    'Services': ['Svcs', 'Srvcs'],
    'School ': ['Schl '],
    'Sciences ': ['Sci '],
    'Technology': ['Tech.']
}

# Partial/substring words in college, department and organization names
# that must always be lowercase in Unit names.
UNIT_NAME_LOWERCASE_REPLACEMENTS = [
    'and', 'of', 'for', 'in', 'at'
]

# Partial/substring words in college, department and organization names
# that must always be uppercase in Unit names.
UNIT_NAME_UPPERCASE_REPLACEMENTS = [
    'AVP', 'BRIDG', 'CHAMPS', 'CREATE', 'FM', 'GTA', 'HRIS', 'IT',
    'LETTR', 'LINK', 'NASA', 'RESTORES', 'ROTC', 'STAT', 'TV',
    'TV/FM', 'UCF', 'WUCF',
]
