from django.core.management.base import BaseCommand
from django.utils import timezone
from images.models import *

import sys
import math
import logging
import re
import timeit
import datetime

import requests
from PIL import Image as PILImage
from PIL import ExifTags
import io
from progress.bar import Bar
from dateutil.parser import *
import boto3


class TandemVault(object):
    """
    Handles requests to Tandem Vault's API and stores responses
    """
    domain = ''
    admin_api_key = ''
    communicator_api_key = ''

    per_page_max = 0  # Max number of expected results per page
    total_page_count = 0  # total number of paged Tandem Vault API results
    total_assets = 0  # total number of assets in Tandem Vault API results
    pages = []
    uploadsets = {}
    start_date = None
    end_date = None

    api_base_assets_path = '/api/v1/assets/'
    api_base_asset_path = '/api/v1/assets/{0}/'
    api_base_download_path = '/assets/{0}/'
    api_base_uploadset_path = '/api/v1/upload_sets/{0}/'
    api_assets_url = ''
    api_asset_url = ''
    api_download_url = ''
    api_uploadset_url = ''
    api_assets_params = {}
    api_asset_params = {}
    api_uploadset_params = {}

    def __init__(self, domain, admin_api_key, communicator_api_key, start_date, end_date):
        self.domain = domain
        self.admin_api_key = admin_api_key
        self.communicator_api_key = communicator_api_key
        self.start_date = start_date
        self.end_date = end_date

        self.api_assets_url = 'https://{0}{1}'.format(
            self.domain,
            self.api_base_assets_path
        )
        self.api_asset_url = 'https://{0}{1}'.format(
            self.domain,
            self.api_base_asset_path
        )
        self.api_download_url = 'https://{0}{1}'.format(
            self.domain,
            self.api_base_download_path
        )
        self.api_uploadset_url = 'https://{0}{1}'.format(
            self.domain,
            self.api_base_uploadset_path
        )

        self.api_assets_params = {
            'api_key': self.communicator_api_key,
            'state': 'accepted',
            'date[start(1i)]': self.start_date.year,
            'date[start(2i)]': self.start_date.month,
            'date[start(3i)]': self.start_date.day,
            'date[end(1i)]': self.end_date.year,
            'date[end(2i)]': self.end_date.month,
            'date[end(3i)]': self.end_date.day,
        }
        self.api_asset_params = {
            'api_key': self.communicator_api_key
        }
        self.api_uploadset_params = {
            # upload_set API requires elevated permissions
            'api_key': self.admin_api_key
        }

        # Fetch the first page of results, which will set the total number
        # of results and total page count:
        self.pages.append(self.fetch_assets_page(1))

    def fetch_assets_page(self, page):
        """
        Fetches a single page of results on the Tandem Vault assets API
        and returns the corresponding JSON data.
        """
        params = self.api_assets_params.copy()
        params.update({
            'page': page
        })

        response_json = None

        try:
            response = requests.get(
                self.api_assets_url,
                params=params
            )
            response.raise_for_status()  # Raise exception if 4xx/5xx server error
            response_json = response.json()

            # Set some required properties if
            # this is the first page request:
            if page == 1 and len(response_json) > 0:
                # Assume the number of results on the first page
                # represents the max number of expected results
                # on all subsequent page requests:
                self.per_page_max = len(response_json)
                self.total_assets = int(
                    response.headers['total-results']
                )
                self.total_page_count = int(math.ceil(
                    self.total_assets / self.per_page_max
                ))

            # Strip non-image results from response
            # response_json = [asset for asset in response_json if asset.get('type', None) == 'Image']
        except Exception as e:
            logging.warning(
                '\nError retrieving assets page data: {0}'
                .format(e)
            )

        return response_json

    def fetch_asset(self, asset_id):
        """
        Fetches an API result for a single Tandem Vault image.
        """
        response_json = None

        try:
            response = requests.get(
                self.api_asset_url.format(asset_id),
                params=self.api_asset_params
            )
            response_json = response.json()

            if response_json.get('error', None):
                logging.warning(
                    '\nError returned by single asset data: {0}'
                    .format(response_json['error'])
                )
                response_json = None
        except Exception as e:
            logging.warning(
                '\nError retrieving single asset data: {0}'
                .format(e)
            )

        return response_json

    def fetch_uploadset(self, uploadset_id):
        """
        Fetches an API result for a single Tandem Vault upload set.
        Stores data for later use to avoid subsequent API calls when possible.
        """
        response_json = None

        # Retrieve existing data if possible
        try:
            response_json = self.uploadsets[uploadset_id]
        except KeyError:
            try:
                response = requests.get(
                    self.api_uploadset_url.format(uploadset_id),
                    params=self.api_uploadset_params
                )
                response_json = response.json()

                if response_json.get('error', None):
                    logging.warning(
                        '\nError returned by single upload set data: {0}'
                        .format(response_json['error'])
                    )
                    response_json = None
                else:
                    # Store retrieved data for later use
                    self.uploadsets.update(
                        {uploadset_id: response_json}
                    )
            except Exception as e:
                logging.warning(
                    '\nError retrieving single upload set data: {0}'
                    .format(e)
                )

        return response_json

    def fetch_image_data(self, progress):
        """
        Retrieves all pages of image data, starting from
        page 2.
        """
        if self.total_page_count > 1:
            # for page in range(2, 6):  # TODO for debugging only
            for page in range(2, self.total_page_count):
                self.pages.append(self.fetch_assets_page(page))

                if progress:
                    progress.next()

    def get_uploadset_id(self, thumb_url):
        """
        Returns the extrapolated upload set ID from a provided
        Tandem Vault thumbnail URL.
        """
        try:
            # Given a thumbnail URL from Tandem Vault, the upload set ID
            # is the first series of numbers after the domain name:
            # https://x.y.z/<upload_set_id>/<image_id>/1/<browse OR grid OR thumb>/<image_catalogue_number>.ext
            upload_set_id = int(
                re.search(
                    '^https://[a-zA-Z0-9-.]+/([0-9]+)/',
                    thumb_url
                )
                .group(1)
            )
        except (AttributeError, TypeError):
            logging.warning(
                (
                    'Could not determine upload set ID from Tandem Vault '
                    'thumbnail URL "{0}"'
                )
                .format(thumb_url)
            )
            upload_set_id = None

        return upload_set_id


class Rekognition(object):
    """
    Handles connecting to AWS and processing of
    image data using Rekognition
    """
    aws_client = None
    confidence_threshold = 'mean-adjusted'
    tag_blacklist = [
        'accessory',
        'accessories',
        'apparel',
        'clothing',
        'dating',
        'furniture',
        'human',
        'mammal'
        'photo',
        'photography',
        'skin'
    ]
    tag_translations = {
        'american football': 'football'
    }

    def __init__(self, aws_access_key, aws_secret_key, aws_region, confidence_threshold):
        self.aws_client = boto3.client(
            'rekognition',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        self.confidence_threshold = confidence_threshold

    def get_image_data(self, image_file):
        """
        Sends an image to AWS Rekognition and returns data about that image.
        """
        data = {
            'labels': [],
            'mean_confidence_score': None
        }

        if image_file is not None:
            # Object and scene detection labels (tags)
            response = self.aws_client.detect_labels(
                Image={'Bytes': image_file}
            )

            for label in response['Labels']:
                # Perform translations for individual labels
                if label['Name'].lower() in self.tag_translations:
                    label['Name'] = self.tag_translations[label['Name'].lower()]

                # Perform blacklisting for individual labels
                if label['Name'].lower() not in self.tag_blacklist:
                    data['labels'].append(label)

            # Calculate mean confidence score if the
            # script's confidence threshold is set to 'mean-adjusted':
            if self.confidence_threshold == 'mean-adjusted':
                mean_score = (
                    sum([label['Confidence']
                         for label in data['labels']]) / len(data['labels'])
                )
                data['labels_mean_confidence_score'] = mean_score

                logging.debug(
                    'Mean tag score for image: {0}'
                    .format(mean_score)
                )

        return data

    def get_image_tags(self, image_file):
        """
        Returns a list of viable tags for the given image_file.
        """
        tags = []
        data = self.get_image_data(image_file)

        if data:
            mean_confidence_score = data['labels_mean_confidence_score']

            for single_tag in data['labels']:
                tag_name = single_tag['Name'].lower().strip()
                tag_score = single_tag['Confidence']

                logging.debug(
                    'Generated tag: {0} | Confidence: {1}'
                    .format(tag_name, tag_score)
                )

                if (
                    self.confidence_threshold_met(
                        tag_score,
                        mean_confidence_score
                    )
                ):
                    tags.append(tag_name)

        return tags

    def confidence_threshold_met(self, confidence_score, mean=80):
        """
        Determines if a tag confidence score meets the required threshold.
        """
        if mean is None:
            mean = 80
        if self.confidence_threshold == 'mean-adjusted':
            if mean < 80:
                mean = 80
            return confidence_score >= mean
        else:
            return confidence_score >= self.confidence_threshold


class ImageData(object):
    """
    Manages information about a Tandem Vault image's data,
    its corresponding Image object, and its tags
    """
    image = None
    image_file = None
    image_json = None
    single_json = None
    uploadset_json = None
    generate_tags = False
    unique_tag_names = []
    tv_tags = []
    rk_tags = []
    tags_created = 0

    def __init__(self, image, image_file, image_json, single_json, uploadset_json, generate_tags):
        self.image = image
        self.image_file = image_file
        self.image_json = image_json
        self.single_json = single_json
        self.uploadset_json = uploadset_json
        self.generate_tags = generate_tags

        # Initialize a unique list of existing tag names to avoid
        # generating duplicates.  Prioritizes tags from any other
        # source besides Tandem Vault and Rekognition (e.g. from
        # the Django admin).
        self.unique_tag_names = set(
            [tag.name.lower() for tag in self.image.tags.exclude(
                source__in=['Tandem Vault', 'AWS Rekognition'])]
        )

    def get_tags(self, rk):
        """
        Assigns tag names to self.tv_tags based on retrieved
        Tandem Vault data.

        Also fetches and assigns generated tags to self.rk_tags
        if tag generation is enabled for this image.
        """
        # Clear existing set tags imported from Tandem Vault if
        # we retrieved single image data/didn't skip it:
        if self.single_json:
            self.image.tags.remove(
                *self.image.tags.filter(source='Tandem Vault'))

        # If Rekognition tagging is enabled,
        # clear existing tag relationships retrieved from Rekognition:
        if self.generate_tags:
            self.image.tags.remove(
                *self.image.tags.filter(source='AWS Rekognition')
            )

        # Get or create fresh tags based on Tandem Vault's
        # tag list for the image, if we retrieved single
        # image data for the image/didn't skip it:
        if self.single_json:
            for tandemvault_tag_name in self.single_json['tag_list']:
                tandemvault_tag_name_lower = tandemvault_tag_name.lower().strip()
                # If this tag doesn't already match the name of another tag
                # assigned to the image, get or create an ImageTag object
                # and assign it to the Image
                if tandemvault_tag_name_lower not in self.unique_tag_names:
                    self.unique_tag_names.append(tandemvault_tag_name_lower)
                    self.tv_tags.append(tandemvault_tag_name)

        # Assign the upload set's name as a tag for the image,
        # if we retrieved upload set information for the image:
        if self.uploadset_json:
            uploadset_tag_name_lower = uploadset_json['title'].lower().strip()
            if uploadset_tag_name_lower not in self.unique_tag_names:
                self.unique_tag_names.append(uploadset_tag_name_lower)
                self.tv_tags.append(uploadset_tag_name)

        # Generate and assign tags from Rekognition:
        if rk and self.generate_tags:
            logging.debug(
                'Generating tags via Rekognition for image: {0}'
                .format(self.image.thumbnail_url)
            )

            rekognition_tags = rk.get_image_tags(self.image_file)
            for rekognition_tag_name in rekognition_tags:
                if rekognition_tag_name not in self.unique_tag_names:
                    self.unique_tag_names.append(rekognition_tag_name)
                    self.rk_tags.append(rekognition_tag_name)

    def assign_tags(self, rk):
        """
        Assigns tags to self.image.
        """
        self.get_tags(rk)

        # Handle Tandem Vault tags:
        for tag in self.tv_tags:
            try:
                tandemvault_tag = ImageTag.objects.get(
                    name=tag
                )
            except ImageTag.DoesNotExist:
                tandemvault_tag = ImageTag(
                    name=tag,
                    source='Tandem Vault'
                )
                tandemvault_tag.save()
                self.tags_created += 1

            self.image.tags.add(tandemvault_tag)

        # Handle Rekognition-generated tags:
        for tag in self.rk_tags:
            try:
                rekognition_tag = ImageTag.objects.get(
                    name=tag
                )
            except ImageTag.DoesNotExist:
                rekognition_tag = ImageTag(
                    name=tag,
                    source='AWS Rekognition'
                )
                rekognition_tag.save()
                self.tags_created += 1

            self.image.tags.add(rekognition_tag)


class Command(BaseCommand):
    help = 'Imports image assets from UCF\'s Tandem Vault instance.'

    tv_page_progress_bar = None
    single_image_progress_bar = None
    aws_access_key = settings.AWS_ACCESS_KEY
    aws_secret_key = settings.AWS_SECRET_KEY
    aws_region = settings.AWS_REGION
    tandemvault_domain = ''
    tandemvault_admin_api_key = ''
    tandemvault_communicator_api_key = ''
    tandemvault_start_date = ''
    tandemvault_end_date = ''
    default_start_date = datetime.date(*settings.IMPORTED_IMAGE_LIMIT)
    default_end_date = timezone.now()
    generate_tags = ''
    tag_confidence_threshold = ''
    preserve_stale_images = False
    delete_stale_tags = False
    loglevel = ''

    photo_taken_exif_key = 36867  # 'DateTimeOriginal' EXIF data key

    modified = None
    imported = None
    exec_time = 0
    exec_start = 0
    exec_end = 0

    images_created = 0
    images_updated = 0
    images_deleted = 0
    images_skipped = 0
    tags_created = 0
    tags_deleted = 0

    rk = None  # Rekognition object
    tv = None  # TandemVault object
    image_data = []  # List of ImageData objects

    def add_arguments(self, parser):
        parser.add_argument(
            '--tandemvault-domain',
            type=str,
            help='The base domain of UCF\'s Tandem Vault',
            dest='tandemvault-domain',
            default=settings.UCF_TANDEMVAULT_DOMAIN,
            required=False
        )
        parser.add_argument(
            '--tandemvault-admin-api-key',
            type=str,
            help='''\
            The API key used to connect to Tandem Vault with
            admin-level user access.
            ''',
            dest='tandemvault-admin-api-key',
            default=settings.TANDEMVAULT_ADMIN_API_KEY,
            required=False
        )
        parser.add_argument(
            '--tandemvault-communicator-api-key',
            type=str,
            help='''\
            The API key used to connect to Tandem Vault with
            UCF Communicator-level user access
            ''',
            dest='tandemvault-communicator-api-key',
            default=settings.TANDEMVAULT_COMMUNICATOR_API_KEY,
            required=False
        )
        parser.add_argument(
            '--start-date',
            type=str,
            help='''\
            Start of a date range by which images should be retrieved
            from Tandem Vault. Expected format: mm-dd-yyyy
            ''',
            dest='start-date',
            default=self.default_start_date.strftime('%m-%d-%Y'),
            required=False
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='''\
            End of a date range by which images should be retrieved
            from Tandem Vault. Expected format: mm-dd-yyyy
            ''',
            dest='end-date',
            default=self.default_end_date.strftime('%m-%d-%Y'),
            required=False
        )
        parser.add_argument(
            '--assign-tags', '--generate-tags',
            type=str,
            help='''\
            Specify what images, if any, should be processed with AWS\'s
            Rekognition services to generate image tags.
            ''',
            dest='generate-tags',
            default='none',
            choices=['all', 'new_modified', 'none'],
            required=False
        )
        parser.add_argument(
            '--tag-confidence-threshold',
            type=str,
            help='''\
            The minimum confidence ranking an automatically-generated
            tag must have to be assigned to an image. Accepts "mean-adjusted"
            (default) or a decimal value between 0 and 100.
            ''',
            dest='tag-confidence-threshold',
            default='mean-adjusted',
            required=False
        )
        parser.add_argument(
            '--number-threads',
            type=int,
            help='''\
            The number of threads to use to concurrently fetch
            Rekognition results
            ''',
            dest='number-threads',
            default=10,
            required=False
        )
        parser.add_argument(
            '--preserve-stale-images',
            help='''\
            If enabled, existing Image objects that are not present in
            the retrieved Tandem Vault data will *not* be deleted.
            ''',
            action='store_true',
            dest='preserve-stale-images',
            default=False,
            required=False
        )
        parser.add_argument(
            '--delete-stale-tags',
            help='''\
            If enabled, existing ImageTag objects that have no assigned
            Images will be deleted (but synonym relationships one level
            deep will be respected).
            ''',
            action='store_true',
            dest='delete-stale-tags',
            default=False,
            required=False
        )
        parser.add_argument(
            '--verbose',
            help='Use verbose logging',
            action='store_const',
            dest='loglevel',
            const=logging.INFO,
            default=logging.WARNING,
            required=False
        )

    def handle(self, *args, **options):
        self.tandemvault_domain = options['tandemvault-domain'].replace(
            'http://', '').replace('https://', '')
        self.tandemvault_admin_api_key = options['tandemvault-admin-api-key']
        self.tandemvault_communicator_api_key = options['tandemvault-communicator-api-key']
        self.tandemvault_start_date = parse(
            options['start-date']) if options['start-date'] else self.default_start_date
        self.tandemvault_end_date = parse(
            options['end-date']) if options['start-date'] else self.default_end_date
        self.generate_tags = options['generate-tags']
        self.tag_confidence_threshold = options['tag-confidence-threshold']
        self.preserve_stale_images = options['preserve-stale-images']
        self.delete_stale_tags = options['delete-stale-tags']
        self.loglevel = options['loglevel']

        # Set logging level
        logging.basicConfig(stream=sys.stdout, level=self.loglevel)

        if (
            not self.tandemvault_admin_api_key
            or not self.tandemvault_communicator_api_key
            or not self.tandemvault_domain
        ):
            print((
                'Tandemvault domain and API keys are required to perform an '
                'import. Update your settings_local.py or provide these '
                'values manually.'
            ))
            return

        if self.generate_tags != 'none' and not self.aws_access_key:
            print((
                'AWS access key ID required to assign tags via Rekognition. '
                'Please set an access key in your settings_local.py file and '
                'try again.'
            ))
            return

        if self.generate_tags != 'none' and not self.aws_secret_key:
            print((
                'AWS secret key required to assign tags via Rekognition. '
                'Please set a secret key in your settings_local.py file '
                'and try again.'
            ))
            return

        if self.generate_tags != 'none':
            if is_float(self.tag_confidence_threshold):
                self.tag_confidence_threshold = float(
                    self.tag_confidence_threshold)
                if (
                    self.tag_confidence_threshold > 100
                    or self.tag_confidence_threshold < 0
                ):
                    print((
                        'Tag confidence threshold value must be either '
                        '"mean-adjusted" or a value between 0 and 100'
                    ))
                    return
            elif self.tag_confidence_threshold != 'mean-adjusted':
                print((
                    'Tag confidence threshold value must be either '
                    '"mean-adjusted" or a value between 0 and 100'
                ))
                return

        now = timezone.now()
        self.modified = now
        self.imported = now

        # Start a timer for the bulk of the script
        self.exec_start = timeit.default_timer()

        # If enabled, set up a client for interfacing with AWS:
        if self.generate_tags != 'none':
            try:
                self.rk = Rekognition(
                    aws_access_key=self.aws_access_key,
                    aws_secret_key=self.aws_secret_key,
                    aws_region=self.aws_region,
                    confidence_threshold=self.tag_confidence_threshold
                )
            except Exception as e:
                logging.error('Error establishing client: {0}'.format(e))
                return

        # Fetch + loop through all Tandem Vault API results
        try:
            self.tv = TandemVault(
                domain=self.tandemvault_domain,
                admin_api_key=self.tandemvault_admin_api_key,
                communicator_api_key=self.tandemvault_communicator_api_key,
                start_date=self.tandemvault_start_date,
                end_date=self.tandemvault_end_date
            )
        except Exception as e:
            logging.error(
                'Error connecting to Tandem Vault API: {0}'.format(e))

        # Retrieve all image data from Tandem Vault
        self.tv_page_progress_bar = Bar(
            'Retrieving image data...',
            max=self.tv.total_page_count
        )
        self.tv.fetch_image_data(self.tv_page_progress_bar)
        self.tv_page_progress_bar.finish()

        # Process all the images retrieved from Tandem Vault
        self.single_image_progress_bar = Bar(
            'Processing images...',
            max=self.tv.total_assets
        )
        self.process_images()
        self.single_image_progress_bar.finish()

        # Delete stale images and image tags
        self.delete_stale()

        # Stop timer
        self.exec_end = timeit.default_timer()
        self.exec_time = datetime.timedelta(
            seconds=self.exec_end - self.exec_start
        )

        # Print the results
        self.print_stats()

        return

    def process_images(self):
        """
        The main image processing function that executes all API
        requests and Image + ImageTag object creation.
        """
        # Loop through all retrieved pages, and create/update
        # Image objects (sans tag information)
        for pagenum in range(0, len(self.tv.pages) - 1):
            page_json = self.tv.pages[pagenum]

            if not page_json:
                logging.warning(
                    (
                        'Page {0} of Tandem Vault assets is not set. '
                        'Skipping page.'
                    )
                    .format(pagenum)
                )
                continue

            for asset in page_json:
                asset_type = asset.get('type', None)
                if asset_type == 'Image':
                    single_image_data = self.process_image(asset)
                    if single_image_data is not None:
                        self.image_data.append(single_image_data)

        # Process tag information for each image
        for single_image_data in self.image_data:
            single_image_data.assign_tags(self.rk)
            self.tags_created += single_image_data.tags_created

    def process_image(self, tandemvault_image):
        """
        Processes a single Tandem Vault image.
        Returns an ImageData object
        """
        self.single_image_progress_bar.next()

        download_url = self.tv.api_download_url.format(
            tandemvault_image['id']
        )
        # Use 'browse_url' for thumb instead of 'thumb_url'
        # due to slightly larger size
        thumb_url = tandemvault_image['browse_url']
        uploadset_id = self.tv.get_uploadset_id(thumb_url)
        photo_taken = None
        location = None
        single_json = None
        uploadset_json = None

        logging.debug(
            'Processing image with ID {0}, Download URL {1}'
            .format(tandemvault_image['id'], download_url)
        )

        image_file = None

        # Set up the initial Image object.
        try:
            image = Image.objects.get(
                source='Tandem Vault',
                source_id=tandemvault_image['id']
            )

            # Check if this image has been modified in Tandem Vault since
            # the last time the image was imported into the Search Service.
            # Only retrieve single image details if changes have been
            # made since the last time the Search Service image was imported:
            tandemvault_image_modified = parse(
                tandemvault_image['modified_at']
            )
            if image.last_imported < tandemvault_image_modified:
                # Download thumbnail of image
                image_file = self.download_image(thumb_url)

                # Retrieve photo taken date from EXIF data
                photo_taken = self.get_image_taken_date(image_file)

                # Retrieve upload set data. Allow import to
                # continue if data cannot be retrieved:
                uploadset_json = self.tv.fetch_uploadset(
                    uploadset_id
                )
                if not uploadset_json:
                    logging.warning(
                        (
                            'Failed to retrieve single upload set info with '
                            'ID {0} for Tandem Vault image with ID {1}.'
                        )
                        .format(uploadset_id, tandemvault_image['id'])
                    )
                else:
                    location = uploadset_json['location']

                # Fetch the single API result
                single_json = self.tv.fetch_asset(
                    tandemvault_image['id']
                )
                if not single_json:
                    logging.warning(
                        (
                            'Failed to retrieve single image info for '
                            'Tandem Vault image with ID {0}. Skipping image.'
                        )
                        .format(tandemvault_image['id'])
                    )
                    self.images_skipped += 1
                    return None

                image.filename = single_json['filename']
                image.extension = single_json['ext']
                image.source_created = parse(single_json['created_at'])
                image.source_modified = tandemvault_image_modified
                image.photo_taken = photo_taken
                image.location = location
                image.copyright = single_json['copyright']
                image.contributor = single_json['contributor']['to_s']
                image.width_full = int(single_json['width'])
                image.height_full = int(single_json['height'])
                image.download_url = download_url
                image.thumbnail_url = image_thumb_url
                image.caption = single_json['short_caption']

                self.images_updated += 1
            else:
                if self.generate_tags == 'all':
                    # Download thumbnail of image for Rekognition later
                    image_file = self.download_image(thumb_url)

                    # Continue processing the image without single image
                    # data; allow tagging via Rekognition later:
                    self.images_updated += 1
                    logging.info(
                        (
                            'Skipping retrieval of single image data and '
                            'upload set data for image with ID {0} since '
                            'there are no updates, but still assigning tags '
                            'via Rekognition.'
                        )
                        .format(tandemvault_image['id'])
                    )
                else:
                    image.last_imported = self.imported
                    image.save()

                    # Return here/stop processing the image completely:
                    self.images_skipped += 1
                    logging.info(
                        (
                            'Skipping image with ID {0} entirely, since '
                            'there are no updates.'
                        )
                        .format(tandemvault_image['id'])
                    )
                    return None
        except Image.DoesNotExist:
            # Download thumbnail of image
            image_file = self.download_image(thumb_url)

            # Retrieve photo taken date from EXIF data
            photo_taken = self.get_image_taken_date(image_file)

            # Retrieve upload set data
            uploadset_json = self.tv.fetch_uploadset(uploadset_id)
            if not uploadset_json:
                logging.warning(
                    (
                        'Failed to retrieve single upload set info with '
                        'ID {0} for Tandem Vault image with ID {1}.'
                    )
                    .format(uploadset_id, tandemvault_image['id'])
                )
            else:
                location = uploadset_json['location']

            # Fetch the single API result
            single_json = self.tv.fetch_asset(tandemvault_image['id'])
            if not single_json:
                logging.warning(
                    (
                        'Failed to retrieve single image info for '
                        'Tandem Vault image with ID {0}. Skipping image.'
                    )
                    .format(tandemvault_image['id'])
                )
                self.images_skipped += 1
                return None

            # Create new Image
            image = Image(
                filename=single_json['filename'],
                extension=single_json['ext'],
                source='Tandem Vault',
                source_id=single_json['id'],
                source_created=parse(single_json['created_at']),
                source_modified=parse(single_json['modified_at']),
                photo_taken=photo_taken,
                location=location,
                copyright=single_json['copyright'],
                contributor=single_json['contributor']['to_s'],
                width_full=int(single_json['width']),
                height_full=int(single_json['height']),
                download_url=download_url,
                thumbnail_url=single_json['browse_url'],
                caption=single_json['short_caption']
            )

            self.images_created += 1

        image.last_imported = self.imported
        image.save()

        return ImageData(
            image=image,
            image_file=image_file,
            image_json=tandemvault_image,
            single_json=single_json,
            uploadset_json=uploadset_json,
            generate_tags=self.generate_tags != 'none'
        )

    def download_image(self, image_url):
        image_file = None

        try:
            image_file = requests.get(image_url).content
        except Exception as e:
            logging.warning(
                '\nError downloading image: {0}'
                .format(e)
            )

        return image_file

    def get_image_taken_date(self, image_file):
        taken_date = None

        try:
            pil_img = PILImage.open(io.BytesIO(image_file))
        except Exception as e:
            logging.warning(
                '\nError opening image with Pillow: {0}'
                .format(e)
            )
            return taken_date

        img_exif = pil_img.getexif()
        if img_exif is not None:
            img_exif_dict = dict(img_exif)
            try:
                taken_date_str = img_exif_dict[self.photo_taken_exif_key]
                taken_date = datetime.datetime.strptime(
                    taken_date_str,
                    '%Y:%m:%d %H:%M:%S'
                )
                # Make the parsed date timezone-aware
                taken_date_tz = timezone.make_aware(taken_date)
            except Exception:
                # If the taken date isn't available, or we
                # can't parse it, just move on:
                taken_date_tz = None

        return taken_date_tz

    def print_stats(self):
        """
        Displays information about the import.
        """

        stats = '''\
Finished import of Tandem Vault images.

Images
---------
Created: {0}
Updated: {1}
Deleted: {2}
Skipped: {3}

Image Tags
-------------
Created: {4}
Deleted: {5}

Script executed in {6}
            '''.format(
                self.images_created,
                self.images_updated,
                self.images_deleted,
                self.images_skipped,
                self.tags_created,
                self.tags_deleted,
                self.exec_time
        )

        print(stats)

    def delete_stale(self):
        """
        Deletes Image objects sourced from Tandem Vault that are no
        longer present in Tandem Vault, and deletes ImageTags that
        are not assigned to any Images.

        Uses the --preserve-stale-images and --delete-stale-tags flags
        to determine whether stale objects should be deleted.
        """
        if not self.preserve_stale_images:
            stale_images = Image.objects.filter(
                last_imported__lt=self.imported,
                source='Tandem Vault'
            )
            self.images_deleted = stale_images.count()
            stale_images.delete()

        if self.delete_stale_tags:
            stale_tags = ImageTag.objects.filter(
                synonyms__images__isnull=True).filter(images__isnull=True)
            self.tags_deleted = stale_tags.count()
            stale_tags.delete()


def is_float(value):
    """
    Utility function for determining if a value is translatable into a float.
    """
    try:
        float(value)
        return True
    except ValueError:
        return False
