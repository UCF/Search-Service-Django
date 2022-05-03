from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name='UCF-Search-Service-Django',
    version='2.6.2',
    description='Django API for various UCF data',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/UCF/Search-Service-Django/',
    author='UCF Web Communications',
    author_email='webcom@ucf.edu',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: UCF Community',
        'Topic :: UCF Data :: API',
        'License :: MIT',
        'Programming Language :: Python :: 3 :: Only'
    ],
    packages=find_packages(where='.'),
    install_requires=[
        'beautifulsoup4',
        'boto3',
        'Django==3.2.13',
        'django-cors-headers',
        'djangorestframework',
        'djangorestframework-gis',
        'django-filter',
        'django_mysql',
        'django-storages',
        'django-s3-file-field[boto3]',
        'django-widget-tweaks',
        'drf-dynamic-fields',
        'fuzzywuzzy',
        'gunicorn',
        'lxml==4.6.5',
        'mysqlclient',
        'Pillow==9.0.1',
        'progress',
        # 'psycopg2',
        'python-dateutil',
        'python-Levenshtein',
        'raven',
        'requests',
        'sqlparse==0.4.2',
        'tabulate',
        'Unidecode',
    ],
    python_requires='>=3.6, <4',
    project_urls={
        'Bug Reports': 'https://github.com/UCF/Search-Service-Django/issues',
        'Source': 'https://github.com/UCF/Search-Service-Django/'
    }
)
