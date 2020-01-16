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
import StringIO
from progress.bar import Bar
from dateutil.parser import *
import boto3

from Queue import Queue
from threading import Thread


class ImageData(object):
    """
    Temporary data class for image data
    """
    def __init__(self, image, image_file, tv_tags, process_tags=True):
        """
        Initializes a new instance of ImageData
        :param image: An Image model object
        :param tv_tags: A list of Tandemvault tags
        """
        self.image = image
        self.image_file = image_file
        self.tv_tags = tv_tags
        self.rk_tags = []
        self.process_tags = process_tags


class RekognitionWorker(Thread):
    """
    A worker thread for retrieving
    Rekognition tags
    """
    def __init__(
        self, queue, aws_client, threshold, translations,
        blacklist, results
    ):
        """
        Initializes a new instance of the
        RekognitionWorker object
        :param image: An ImageData object
        """
        Thread.__init__(self)
        self.queue = queue
        self.aws_client = aws_client
        self.threshold = threshold
        self.translations = translations
        self.blacklist = blacklist
        self.results = results

    def run(self):
        while True:
            image_data = self.queue.get()
            try:
                # If we're not processing tags, just return
                # the data unchanged
                if image_data.process_tags is False:
                    self.results.put(image_data)
                else:
                    # If we are processing tags, then let's go!
                    image_data = self.process_rekognition_tags(image_data)
                    self.results.put(image_data)
            except Exception, ex:
                logging.warning(
                    (
                        'There was an exception while processing a '
                        'Rekognition request: {0}'
                    )
                    .format(ex)
                )
            finally:
                self.queue.task_done()

    def get_rekognition_data(self, image_file):
        """
        Sends an image to AWS Rekognition and returns data about that image.
        """
        data = {
            'labels': []
        }

        if image_file is not None:
            # Object and scene detection labels (tags)
            response = self.aws_client.detect_labels(
                Image={'Bytes': image_file}
            )

            for label in response['Labels']:
                # Perform translations for individual labels
                if label['Name'].lower() in self.translations:
                    label['Name'] = self.translations[label['Name'].lower()]

                # Perform blacklisting for individual labels
                if label['Name'].lower() not in self.blacklist:
                    data['labels'].append(label)

            # Calculate mean confidence score if the
            # script's confidence threshold is set to 'mean-adjusted':
            if self.threshold == 'mean-adjusted':
                mean_score = (sum([label['Confidence'] for label in data['labels']]) / len(data['labels']))
                data['labels_mean_confidence_score'] = mean_score

        return data

    def confidence_threshold_met(self, confidence_score, mean=80):
        """
        Determines if a tag confidence score meets the required threshold.
        """
        if self.threshold == 'mean-adjusted':
            if mean < 80:
                mean = 80
            return confidence_score >= mean
        else:
            return confidence_score >= self.threshold

    def process_rekognition_tags(self, image_data):
        image_file = image_data.image_file
        rekognition_data = self.get_rekognition_data(image_file)
        rekognition_tags = []
        rekognition_tag_score_mean = None

        logging.debug(
            'Generating tags for image: {0}'
            .format(image_data.image.thumbnail_url)
        )

        if rekognition_data:
            rekognition_tags = rekognition_data['labels']
            if self.threshold == 'mean-adjusted':
                rekognition_tag_score_mean = rekognition_data['labels_mean_confidence_score']
                logging.debug(
                    'Mean tag score for image: {0}'
                    .format(rekognition_tag_score_mean)
                )

        for rekognition_tag_data in rekognition_tags:
            rekognition_tag_name = rekognition_tag_data['Name'].lower().strip()
            rekognition_tag_score = rekognition_tag_data['Confidence']

            logging.debug(
                'Generated tag: {0} | Confidence: {1}'
                .format(rekognition_tag_name, rekognition_tag_score)
            )

            # If this tag meets our minimum confidence threshold and
            # doesn't already match the name of another tag assigned to
            # the image, get or create an ImageTag object and assign it
            # to the Image:
            if (
                self.confidence_threshold_met(
                    rekognition_tag_score,
                    rekognition_tag_score_mean
                )
                and rekognition_tag_name not in image_data.tv_tags
            ):
                image_data.rk_tags.append(rekognition_tag_name)

        return image_data


class Command(BaseCommand):
    help = 'Imports image assets from UCF\'s Tandem Vault instance.'

    progress_bar = Bar('Processing')
    source = 'Tandem Vault'
    auto_tag_source = 'AWS Rekognition'
    auto_tag_blacklist = [
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
    auto_tag_translations = {
        'american football': 'football'
    }
    default_start_date = datetime.date(*settings.IMPORTED_IMAGE_LIMIT)
    default_end_date = timezone.now()
    tandemvault_assets_api_path = '/api/v1/assets/'
    tandemvault_asset_api_path = '/api/v1/assets/{0}/'
    tandemvault_download_path = '/assets/{0}/'
    tandemvault_upload_set_api_path = '/api/v1/upload_sets/{0}/'
    tandemvault_total_assets = 0  # total number of assets in Tandem Vault API results
    tandemvault_page_count = 0  # total number of paged Tandem Vault API results
    tandemvault_upload_sets = {}  # cached upload set information
    photo_taken_exif_key = 36867  # 'DateTimeOriginal' EXIF data key
    images_created = 0
    images_updated = 0
    images_deleted = 0
    images_skipped = 0
    tags_created = 0
    tags_deleted = 0
    aws_client = None

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
            '--assign-tags',
            type=str,
            help='''\
            Specify what images, if any, should be processed with AWS\'s
            Rekognition services to generate image tags.
            ''',
            dest='assign-tags',
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
        self.tandemvault_domain = options['tandemvault-domain'].replace('http://', '').replace('https://', '')
        self.tandemvault_admin_api_key = options['tandemvault-admin-api-key']
        self.tandemvault_communicator_api_key = options['tandemvault-communicator-api-key']
        self.tandemvault_start_date = parse(options['start-date']) if options['start-date'] else self.default_start_date
        self.tandemvault_end_date = parse(options['end-date']) if options['start-date'] else self.default_end_date
        self.aws_access_key = settings.AWS_ACCESS_KEY
        self.aws_secret_key = settings.AWS_SECRET_KEY
        self.aws_region = settings.AWS_REGION
        self.assign_tags = options['assign-tags']
        self.tag_confidence_threshold = options['tag-confidence-threshold']
        self.number_threads = options['number-threads']
        self.preserve_stale_images = options['preserve-stale-images']
        self.delete_stale_tags = options['delete-stale-tags']
        self.loglevel = options['loglevel']

        # Set logging level
        logging.basicConfig(stream=sys.stdout, level=self.loglevel)
        logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

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

        if self.assign_tags != 'none' and not self.aws_access_key:
            print((
                'AWS access key ID required to assign tags via Rekognition. '
                'Please set an access key in your settings_local.py file and '
                'try again.'
            ))
            return

        if self.assign_tags != 'none' and not self.aws_secret_key:
            print((
                'AWS secret key required to assign tags via Rekognition. '
                'Please set a secret key in your settings_local.py file '
                'and try again.'
            ))
            return

        if self.assign_tags != 'none':
            if is_float(self.tag_confidence_threshold):
                self.tag_confidence_threshold = float(self.tag_confidence_threshold)
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

        self.tandemvault_assets_api_url = (
            'https://'
            + self.tandemvault_domain
            + self.tandemvault_assets_api_path
        )
        self.tandemvault_asset_api_url = (
            'https://'
            + self.tandemvault_domain
            + self.tandemvault_asset_api_path
        )
        self.tandemvault_download_url = (
            'https://'
            + self.tandemvault_domain
            + self.tandemvault_download_path
        )
        self.tandemvault_upload_set_api_url = (
            'https://'
            + self.tandemvault_domain
            + self.tandemvault_upload_set_api_path
        )

        now = timezone.now()
        self.modified = now
        self.imported = now

        self.tandemvault_assets_params = {
            'api_key': self.tandemvault_communicator_api_key,
            'state': 'accepted',
            'date[start(1i)]': self.tandemvault_start_date.year,
            'date[start(2i)]': self.tandemvault_start_date.month,
            'date[start(3i)]': self.tandemvault_start_date.day,
            'date[end(1i)]': self.tandemvault_end_date.year,
            'date[end(2i)]': self.tandemvault_end_date.month,
            'date[end(3i)]': self.tandemvault_end_date.day,
        }
        self.tandemvault_asset_params = {
            'api_key': self.tandemvault_communicator_api_key
        }
        self.tandemvault_upload_set_params = {
            # upload_set API requires elevated permissions
            'api_key': self.tandemvault_admin_api_key
        }

        # Start a timer for the bulk of the script
        self.exec_time = 0
        self.exec_start = timeit.default_timer()

        # If enabled, set up a client for interfacing with AWS:
        if self.assign_tags != 'none':
            try:
                self.aws_client = boto3.client(
                    'rekognition',
                    aws_access_key_id=self.aws_access_key,
                    aws_secret_access_key=self.aws_secret_key,
                    region_name=self.aws_region
                )
            except Exception, e:
                logging.error('Error establishing client: {0}'.format(e))
                return

        # Fetch + loop through all Tandem Vault API results
        self.process_images()

        # Delete stale images and image tags
        self.delete_stale()

        # Stop timer
        self.exec_end = timeit.default_timer()
        self.exec_time = datetime.timedelta(
            seconds=self.exec_end - self.exec_start
        )

        # Print the results
        self.progress_bar.finish()
        self.print_stats()

        return

    def process_images(self):
        """
        The main image processing function that executes all API
        requests and Image + ImageTag object creation.
        """
        # Fetch the first page of results, which will set the total number
        # of results and total page count:
        self.process_tandemvault_assets_page(1)

        # Loop through the other pages of results:
        if self.tandemvault_page_count > 1:
            for page in range(2, self.tandemvault_page_count):
                self.process_tandemvault_assets_page(page)

    def process_tags(self, images):
        """
        Processes the tags assigned to the image
        """

        # Let's do the tandemvault tags first
        for image_data in images:
            for tag in image_data.tv_tags:
                try:
                    tandemvault_tag = ImageTag.objects.get(
                        name=tag
                    )
                except ImageTag.DoesNotExist:
                    tandemvault_tag = ImageTag(
                        name=tag,
                        source=self.source
                    )
                    tandemvault_tag.save()
                    self.tags_created += 1

                image_data.image.tags.add(tandemvault_tag)

            for tag in image_data.rk_tags:
                try:
                    rekognition_tag = ImageTag.objects.get(
                        name=tag
                    )
                except ImageTag.DoesNotExist:
                    rekognition_tag = ImageTag(
                        name=tag,
                        source=self.auto_tag_source
                    )
                    rekognition_tag.save()
                    self.tags_created += 1

                image_data.image.tags.add(rekognition_tag)

    def process_tandemvault_assets_page(self, page):
        """
        Fetches and loops through a single page of assets
        from the Tandem Vault API.
        """
        # Fetch the page:
        page_json = self.fetch_tandemvault_assets_page(page)

        if not page_json:
            logging.warning(
                (
                    'Failed to retrieve page {0} of '
                    'Tandem Vault assets. Skipping assets.'
                )
                .format(page)
            )
            return

        image_queue = Queue()
        image_list = Queue()

        for asset in page_json:
            asset_type = asset.get('type', None)
            if asset_type == 'Image':
                img_data = self.process_image(asset)
                if img_data is not None:
                    image_queue.put(img_data)

        for x in range(self.number_threads):
            worker = RekognitionWorker(
                image_queue,
                self.aws_client,
                self.tag_confidence_threshold,
                self.auto_tag_translations,
                self.auto_tag_blacklist,
                image_list)
            worker.daemon = True
            worker.start()

        image_queue.join()

        retval = list(image_list.queue)

        self.process_tags(retval)

    def process_image(self, tandemvault_image):
        """
        Processes a single Tandem Vault image.
        Returns an ImageData object
        """
        self.progress_bar.next()

        download_url = self.tandemvault_download_url.format(tandemvault_image['id'])
        # Use 'browse_url' for thumb instead of 'thumb_url'
        # due to slightly larger size
        thumb_url = tandemvault_image['browse_url']
        upload_set_id = self.get_tandemvault_upload_set_id(thumb_url)
        photo_taken = None
        location = None
        single_json = None
        upload_set_json = None

        logging.debug(
            'Processing image with ID {0}, Download URL {1}'
            .format(tandemvault_image['id'], download_url)
        )

        process_tags = False
        image_file = None

        # Set up the initial Image object.
        try:
            image = Image.objects.get(
                source=self.source,
                source_id=tandemvault_image['id']
            )

            # Check if this image has been modified in Tandem Vault since
            # the last time the image was imported into the Search Service.
            # Only retrieve single image details if changes have been
            # made since the last time the Search Service image was imported:
            tandemvault_image_modified = parse(tandemvault_image['modified_at'])
            if image.last_imported < tandemvault_image_modified:
                process_tags = True

                # Download thumbnail of image
                image_file = self.download_tandemvault_image(thumb_url)

                # Retrieve photo taken date from EXIF data
                photo_taken = self.get_tandemvault_image_taken_date(image_file)

                # Retrieve upload set data. Allow import to
                # continue if data cannot be retrieved:
                upload_set_json = self.fetch_tandemvault_upload_set(upload_set_id)
                if not upload_set_json:
                    logging.warning(
                        (
                            'Failed to retrieve single upload set info with '
                            'ID {0} for Tandem Vault image with ID {1}.'
                        )
                        .format(upload_set_id, tandemvault_image['id'])
                    )
                else:
                    location = upload_set_json['location']

                # Fetch the single API result
                single_json = self.fetch_tandemvault_asset(tandemvault_image['id'])
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
                if self.assign_tags == 'all':
                    process_tags = True

                    # Download thumbnail of image for Rekognition later
                    image_file = self.download_tandemvault_image(thumb_url)

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
            process_tags = True

            # Download thumbnail of image
            image_file = self.download_tandemvault_image(thumb_url)

            # Retrieve photo taken date from EXIF data
            photo_taken = self.get_tandemvault_image_taken_date(image_file)

            # Retrieve upload set data
            upload_set_json = self.fetch_tandemvault_upload_set(upload_set_id)
            if not upload_set_json:
                logging.warning(
                    (
                        'Failed to retrieve single upload set info with '
                        'ID {0} for Tandem Vault image with ID {1}.'
                    )
                    .format(upload_set_id, tandemvault_image['id'])
                )
            else:
                location = upload_set_json['location']

            # Fetch the single API result
            single_json = self.fetch_tandemvault_asset(tandemvault_image['id'])
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
                source=self.source,
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

        # Clear existing set tags imported from Tandem Vault if
        # we retrieved single image data/didn't skip it:
        if single_json:
            image.tags.remove(*image.tags.filter(source=self.source))

        # If Rekognition tagging is enabled,
        # clear existing tag relationships retrieved from Rekognition:
        if self.assign_tags != 'none':
            image.tags.remove(*image.tags.filter(source=self.auto_tag_source))

        # Create a unique list of existing tag names to avoid
        # generating duplicates.  Prioritize tags from any other
        # source besides Tandem Vault and Rekognition.
        tag_names_unique = set([tag.name.lower() for tag in image.tags.all()])

        # Get or create fresh ImageTags based on Tandem Vault's
        # tag list for the image, if we retrieved single
        # image data for the image/didn't skip it:
        if single_json:
            for tandemvault_tag_name in single_json['tag_list']:
                tandemvault_tag_name_lower = tandemvault_tag_name.lower().strip()
                # If this tag doesn't already match the name of another tag
                # assigned to the image, get or create an ImageTag object
                # and assign it to the Image
                if tandemvault_tag_name_lower not in tag_names_unique:
                    tag_names_unique.add(tandemvault_tag_name_lower)

        # Assign the upload set's name as a tag for the image,
        # if we retrieved upload set information for the image:
        if upload_set_json:
            upload_set_tag_name_lower = upload_set_json['title'].lower().strip()
            if upload_set_tag_name_lower not in tag_names_unique:
                tag_names_unique.add(upload_set_tag_name_lower)

        image.save()

        return ImageData(
            image,
            image_file,
            tag_names_unique,
            process_tags
        )

    def fetch_tandemvault_assets_page(self, page):
        """
        Fetches a single page of results on the Tandem Vault assets API.
        """
        params = self.tandemvault_assets_params.copy()
        params.update({
            'page': page
        })

        response_json = None

        try:
            response = requests.get(
                self.tandemvault_assets_api_url,
                params=params
            )
            response_json = response.json()

            # Set some required importer properties if
            # this is the first page request:
            if page == 1:
                self.tandemvault_total_assets = int(response.headers['total-results'])
                self.tandemvault_page_count = math.ceil(
                    self.tandemvault_total_assets / len(response_json)
                )
                self.progress_bar.max = self.tandemvault_total_assets
        except Exception, e:
            logging.warning(
                '\nError retrieving assets page data: {0}'
                .format(e)
            )

        return response_json

    def fetch_tandemvault_asset(self, tandemvault_image_id):
        """
        Fetches an API result for a single Tandem Vault image.
        """
        response_json = None

        try:
            response = requests.get(
                self.tandemvault_asset_api_url.format(tandemvault_image_id),
                params=self.tandemvault_asset_params
            )
            response_json = response.json()

            if response_json.get('error', None):
                logging.warning(
                    '\nError returned by single asset data: {0}'
                    .format(response_json['error'])
                )
                response_json = None
        except Exception, e:
            logging.warning(
                '\nError retrieving single asset data: {0}'
                .format(e)
            )

        return response_json

    def fetch_tandemvault_upload_set(self, upload_set_id):
        """
        Fetches an API result for a single Tandem Vault upload set.
        Stores data for later use to avoid subsequent API calls when possible.
        """
        response_json = None

        # Retrieve existing data if possible
        try:
            response_json = self.tandemvault_upload_sets[upload_set_id]
        except KeyError:
            try:
                response = requests.get(
                    self.tandemvault_upload_set_api_url.format(upload_set_id),
                    params=self.tandemvault_upload_set_params
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
                    self.tandemvault_upload_sets.update(
                        {upload_set_id: response_json}
                    )
            except Exception, e:
                logging.warning(
                    '\nError retrieving single upload set data: {0}'
                    .format(e)
                )

        return response_json

    def get_tandemvault_upload_set_id(self, thumb_url):
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

    def download_tandemvault_image(self, image_url):
        image_file = None

        try:
            image_file = requests.get(image_url).content
        except Exception, e:
            logging.warning(
                '\nError downloading image from Tandem Vault: {0}'
                .format(e)
            )

        return image_file

    def get_tandemvault_image_taken_date(self, image_file):
        taken_date = None

        try:
            pil_img = PILImage.open(StringIO.StringIO(image_file))
        except Exception, e:
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
                source=self.source
            )
            self.images_deleted = stale_images.count()
            stale_images.delete()

        if self.delete_stale_tags:
            stale_tags = ImageTag.objects.filter(synonyms__images__isnull=True).filter(images__isnull=True)
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
