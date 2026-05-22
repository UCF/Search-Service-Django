from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

class LocationImageStorage(S3Boto3Storage):
    location = f'{settings.S3_ENV}/media/locations'
    file_overwrite = True
