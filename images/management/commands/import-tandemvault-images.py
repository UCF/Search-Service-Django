from django.core.management.base import BaseCommand
from django.utils import timezone
from images.models import *

import math
import logging
import timeit
import datetime

import requests
from progress.bar import Bar
from dateutil.parser import *
import boto3

from multiprocessing.pool import Pool

class Command(BaseCommand):
    help = 'Imports image assets from UCF\'s Tandem Vault instance.'

    progress_bar                = Bar('Processing')
    source                      = 'Tandem Vault'
    auto_tag_source             = 'AWS Rekognition'
    auto_tag_blacklist          = [
        'human',
        'apparel',
        'clothing',
        'skin',
        'dating',
        'photo',
        'photography',
        'mammal'
    ]
    auto_tag_translations       = {
        'american football': 'football'
    }
    tandemvault_assets_api_path = '/api/v1/assets/'
    tandemvault_asset_api_path  = '/api/v1/assets/{0}/'
    tandemvault_download_path   = '/assets/{0}/'
    tandemvault_total_images    = 0 # total number of images in Tandem Vault API results
    tandemvault_page_count      = 0 # total number of paged Tandem Vault API results
    images_created              = 0
    images_updated              = 0
    images_deleted              = 0
    images_skipped              = 0
    tags_created                = 0
    tags_deleted                = 0

    def add_arguments(self, parser):
        parser.add_argument(
            '--tandemvault-domain',
            type=str,
            help='The base domain of UCF\'s Tandem Vault',
            dest='tandemvault-domain',
            default=settings.UCF_TANDEMVAULT_DOMAIN,
            required=False
        ),
        parser.add_argument(
            '--tandemvault-api-key',
            type=str,
            help='The API key used to connect to Tandem Vault',
            dest='tandemvault-api-key',
            default=settings.TANDEMVAULT_API_KEY,
            required=False
        ),
        parser.add_argument(
            '--assign-tags',
            type=str,
            help='Specify what images, if any, should be processed with AWS\'s Rekognition services to generate image tags.',
            dest='assign-tags',
            default='none',
            choices=['all', 'new_modified', 'none'],
            required=False
        ),
        parser.add_argument(
            '--tag-confidence-threshold',
            type=str,
            help='The minimum confidence ranking an automatically-generated tag must have to be assigned to an image. Accepts "mean-adjusted" (default) or a decimal value between 0 and 100.',
            dest='tag-confidence-threshold',
            default='mean-adjusted',
            required=False
        ),
        parser.add_argument(
            '--number-threads',
            type=int,
            help='The number of threads to use to concurrently fetch Rekognition results',
            dest='number-threads',
            default=10,
            required=False
        )

    def handle(self, *args, **options):
        self.tandemvault_domain = options['tandemvault-domain'].replace('http://', '').replace('https://', '')
        self.tandemvault_api_key = options['tandemvault-api-key']
        self.aws_access_key = settings.AWS_ACCESS_KEY
        self.aws_secret_key = settings.AWS_SECRET_KEY
        self.aws_region = settings.AWS_REGION
        self.assign_tags = options['assign-tags']
        self.tag_confidence_threshold = options['tag-confidence-threshold']
        self.number_threads = options['number-threads']

        if not self.tandemvault_api_key or not self.tandemvault_domain:
            print 'Tandemvault domain and API key are required to perform an import. Update your settings_local.py or provide these values manually.'
            return

        if self.assign_tags != 'none' and not self.aws_access_key:
            print 'AWS access key ID required to assign tags via Rekognition. Please set an access key in your settings_local.py file and try again.'
            return

        if self.assign_tags != 'none' and not self.aws_secret_key:
            print 'AWS secret key required to assign tags via Rekognition. Please set a secret key in your settings_local.py file and try again.'
            return

        if self.assign_tags != 'none':
            if is_float(self.tag_confidence_threshold):
                self.tag_confidence_threshold = float(self.tag_confidence_threshold)
                if self.tag_confidence_threshold > 100 or self.tag_confidence_threshold < 0:
                    print 'Tag confidence threshold value must be either "mean-adjusted" or a value between 0 and 100'
                    return
            elif self.tag_confidence_threshold != 'mean-adjusted':
                print 'Tag confidence threshold value must be either "mean-adjusted" or a value between 0 and 100'
                return

        self.tandemvault_assets_api_url = 'https://' + self.tandemvault_domain + self.tandemvault_assets_api_path
        self.tandemvault_asset_api_url = 'https://' + self.tandemvault_domain + self.tandemvault_asset_api_path
        self.tandemvault_download_url = 'https://' + self.tandemvault_domain + self.tandemvault_download_path

        now = timezone.now()
        self.modified = now
        self.imported = now

        self.tandemvault_assets_params = {
            'api_key': self.tandemvault_api_key,
            'state': 'accepted',
            'date[start(1i)]': settings.IMPORTED_IMAGE_LIMIT[0],
            'date[start(2i)]': settings.IMPORTED_IMAGE_LIMIT[1],
            'date[start(3i)]': settings.IMPORTED_IMAGE_LIMIT[2],
            'date[end(1i)]': self.modified.year,
            'date[end(2i)]': self.modified.month,
            'date[end(3i)]': self.modified.day
        }
        self.tandemvault_asset_params = {
            'api_key': self.tandemvault_api_key
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
                logging.error('ERROR establishing client: %s' % e)
                return

        # Fetch + loop through all Tandem Vault API results
        self.process_images()

        # Delete stale images and image tags
        self.delete_stale()

        # Stop timer
        self.exec_end = timeit.default_timer()
        self.exec_time = datetime.timedelta(seconds=self.exec_end - self.exec_start)

        # Print the results
        self.progress_bar.finish()
        self.print_stats()

        return

    '''
    The main image processing function that executes all API
    requests and Image + ImageTag object creation.
    '''
    def process_images(self):
        # Fetch the first page of results, which will set the total number
        # of results and total page count:
        self.process_tandemvault_assets_page(1)

        # Loop through the other pages of results:
        # if self.tandemvault_page_count > 1:
            # for page in range(2, self.tandemvault_page_count):
                # self.process_tandemvault_assets_page(page)

    '''
    Fetches and loops through a single page of assets
    from the Tandem Vault API.
    '''
    def process_tandemvault_assets_page(self, page):
        # Fetch the page:
        page_json = self.fetch_tandemvault_assets_page(page)

        if not page_json:
            logging.warning('Failed to retrieve page %d of Tandem Vault assets. Skipping images.' % page)
            return

        with Pool(self.number_threads) as p:
            p.map(self.process_image, page_json)

    '''
    Processes a single Tandem Vault image.
    '''
    def process_image(self, tandemvault_image):
        self.progress_bar.next()

        download_url = self.tandemvault_download_url.format(tandemvault_image['id'])
        single_json = None

        logging.debug("Processing image with ID %s, Download URL %s" % (tandemvault_image['id'], download_url))

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
            if image.last_imported < parse(tandemvault_image['modified_at']):
                # Fetch the single API result
                single_json = self.fetch_tandemvault_asset(tandemvault_image['id'])
                if not single_json:
                    logging.warning('Failed to retrieve single image info for Tandem Vault image with ID %d. Skipping image.' % tandemvault_image['id'])
                    self.images_skipped += 1
                    return

                image.filename = single_json['filename']
                image.extension = single_json['ext']
                image.copyright = single_json['copyright']
                image.contributor = single_json['contributor']['to_s']
                image.width_full = int(single_json['width'])
                image.height_full = int(single_json['height'])
                image.download_url = download_url
                image.thumbnail_url = single_json['browse_url'] # use 'browse_url' instead of 'thumb_url' due to slightly larger size
                image.caption = single_json['short_caption']

                self.images_updated += 1
            else:
                if self.assign_tags == 'all':
                    # Continue processing the image without single image
                    # data; allow tagging via Rekognition later:
                    self.images_updated += 1
                    logging.info('Skipping retrieval of single image data for image with ID %d since there are no updates, but still assigning tags via Rekognition.' % tandemvault_image['id'])
                else:
                    image.last_imported = self.imported
                    image.save()

                    # Return here/stop processing the image completely:
                    self.images_skipped += 1
                    logging.info('Skipping image with ID %d entirely, since there are no updates.' % tandemvault_image['id'])
                    return
        except Image.DoesNotExist:
            # Fetch the single API result
            single_json = self.fetch_tandemvault_asset(tandemvault_image['id'])
            if not single_json:
                logging.warning('Failed to retrieve single image info for Tandem Vault image with ID %d. Skipping image.' % tandemvault_image['id'])
                self.images_skipped += 1
                return

            # Create new Image
            image = Image(
                filename = single_json['filename'],
                extension = single_json['ext'],
                source = self.source,
                source_id = single_json['id'],
                copyright = single_json['copyright'],
                contributor=single_json['contributor']['to_s'],
                width_full = int(single_json['width']),
                height_full = int(single_json['height']),
                download_url = download_url,
                thumbnail_url = single_json['browse_url'],
                caption = single_json['short_caption']
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

                    try:
                        tandemvault_tag = ImageTag.objects.get(
                            name=tandemvault_tag_name_lower
                        )
                    except ImageTag.DoesNotExist:
                        tandemvault_tag = ImageTag(
                            name=tandemvault_tag_name_lower,
                            source=self.source
                        )
                        tandemvault_tag.save()
                        self.tags_created += 1

                    image.tags.add(tandemvault_tag)

        # If Rekognition tagging is enabled,
        # send the image to Rekognition:
        if self.assign_tags != 'none':
            rekognition_data = self.get_rekognition_data(image.thumbnail_url)
            rekognition_tags = []
            rekognition_tag_score_mean = None

            logging.debug("GENERATING TAGS FOR IMAGE: %s" % (image.thumbnail_url))

            if rekognition_data:
                rekognition_tags = rekognition_data['labels']
                if self.tag_confidence_threshold == 'mean-adjusted':
                    rekognition_tag_score_mean = rekognition_data['labels_mean_confidence_score']
                    logging.debug("MEAN TAG SCORE FOR IMAGE: %s" % (
                        rekognition_tag_score_mean
                    ))

            for rekognition_tag_data in rekognition_tags:
                rekognition_tag_name = rekognition_tag_data['Name'].lower().strip()
                rekognition_tag_score = rekognition_tag_data['Confidence']

                logging.debug("GENERATED TAG: %s | CONFIDENCE: %s" % (rekognition_tag_name, rekognition_tag_score))

                # If this tag meets our minimum confidence threshold and
                # doesn't already match the name of another tag assigned to
                # the image, get or create an ImageTag object and assign it
                # to the Image:
                if self.confidence_threshold_met(rekognition_tag_score, rekognition_tag_score_mean) and rekognition_tag_name not in tag_names_unique:
                    tag_names_unique.add(rekognition_tag_name)

                    try:
                        rekognition_tag = ImageTag.objects.get(
                            name=rekognition_tag_name
                        )
                    except ImageTag.DoesNotExist:
                        rekognition_tag = ImageTag(
                            name=rekognition_tag_name,
                            source=self.auto_tag_source
                        )
                        rekognition_tag.save()
                        self.tags_created += 1

                    image.tags.add(rekognition_tag)

        image.save()

    '''
    Fetches a single page of results on the Tandem Vault assets API.
    '''
    def fetch_tandemvault_assets_page(self, page):
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
                self.tandemvault_total_images = int(response.headers['total-results'])
                self.tandemvault_page_count = math.ceil(self.tandemvault_total_images / len(response_json))
                self.progress_bar.max = self.tandemvault_total_images
        except Exception, e:
            logging.warning('\nERROR retrieving assets page data: %s' % e)

        return response_json

    '''
    Fetches an API result for a single Tandem Vault image.
    '''
    def fetch_tandemvault_asset(self, tandemvault_image_id):
        response_json = None

        try:
            response = requests.get(
                self.tandemvault_asset_api_url.format(tandemvault_image_id),
                params=self.tandemvault_asset_params
            )
            response_json = response.json()
        except Exception, e:
            logging.warning('\nERROR retrieving single asset data: %s' % e)

        return response_json

    '''
    Sends an image to AWS Rekognition and returns data about that image.
    '''
    def get_rekognition_data(self, image_url):
        data = {
            'labels': []
        }

        try:
            image_data = requests.get(image_url).content
        except Exception, e:
            logging.warning('\nERROR downloading single image: %s' % e)

        if image_data:
            # Object and scene detection labels (tags)
            response = self.aws_client.detect_labels(
                Image={'Bytes': image_data}
            )

            for label in response['Labels']:
                # Perform translations for individual labels
                if label['Name'].lower() in self.auto_tag_translations:
                    label['Name'] = self.auto_tag_translations[label['Name'].lower()]

                # Perform blacklisting for individual labels
                if label['Name'].lower() not in self.auto_tag_blacklist:
                    data['labels'].append(label)

            # Calculate mean confidence score if the
            # script's confidence threshold is set to 'mean-adjusted':
            if self.tag_confidence_threshold == 'mean-adjusted':
                mean_score = ( sum([label['Confidence'] for label in data['labels']]) / len(data['labels']) )
                data['labels_mean_confidence_score'] = mean_score

        return data

    '''
    Determines if a tag confidence score meets the required threshold.
    '''
    def confidence_threshold_met(self, confidence_score, mean=80):
        if self.tag_confidence_threshold == 'mean-adjusted':
            if mean < 80:
                mean = 80
            return confidence_score >= mean
        else:
            return confidence_score >= self.tag_confidence_threshold


    '''
    Displays information about the import.
    '''
    def print_stats(self):
        stats = """
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
        """.format(
            self.images_created,
            self.images_updated,
            self.images_deleted,
            self.images_skipped,
            self.tags_created,
            self.tags_deleted,
            self.exec_time
        )

        print(stats)

    '''
    Deletes Image objects sourced from Tandem Vault that are no
    longer present in Tandem Vault, and deletes ImageTags that
    are not assigned to any Images.

    ** NOTE: stale tag deletion is commented out for now, until
    we can create a complete set of image + Tandem Vault tag data
    in the search service
    '''
    def delete_stale(self):
        stale_images = Image.objects.filter(
            last_imported__lt=self.imported,
            source=self.source
        )
        # stale_tags = ImageTag.objects.filter(images=None)

        self.images_deleted = stale_images.count()
        # self.tags_deleted = stale_tags.count()

        stale_images.delete()
        # stale_tags.delete()


'''
Utility function for determining if a value is translatable into a float.
'''
def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False
