"""
Purges paths from the Azure Front Door cache, so an import's changes
appear without waiting out the TTLs in CACHE_CONTROL_TTLS.

Authenticates as the container's managed identity, through the token
endpoint App Service and Container Apps provide in IDENTITY_ENDPOINT
and IDENTITY_HEADER. The identity needs permission to purge the Front
Door endpoint, such as the CDN Endpoint Contributor role.
"""
import os

import requests
from django.conf import settings

MANAGEMENT_RESOURCE = 'https://management.azure.com/'
TOKEN_API_VERSION = '2019-08-01'
PURGE_API_VERSION = '2025-04-15'
PURGE_URL = (
    'https://management.azure.com/subscriptions/{subscription_id}'
    '/resourceGroups/{resource_group}/providers/Microsoft.Cdn'
    '/profiles/{profile}/afdEndpoints/{endpoint}/purge'
)
TIMEOUT = 30


class PurgeError(Exception):
    pass


def is_configured():
    return bool(settings.FRONT_DOOR)


def purge(paths):
    """
    Asks Front Door to purge the paths, such as '/api/v1/research/*'.
    Front Door finishes the purge in the background, usually within a
    few minutes. Returns False without doing anything when FRONT_DOOR
    isn't configured, as when running locally.
    """
    if not is_configured():
        return False

    config = settings.FRONT_DOOR
    body = {'contentPaths': list(paths)}

    if config.get('domains'):
        body['domains'] = config['domains']

    response = requests.post(
        PURGE_URL.format(**config),
        params={'api-version': PURGE_API_VERSION},
        headers={'Authorization': f'Bearer {get_token()}'},
        json=body,
        timeout=TIMEOUT
    )

    if response.status_code not in (200, 202):
        raise PurgeError(f'Front Door purge failed ({response.status_code}): {response.text}')

    return True


def get_token():
    endpoint = os.environ.get('IDENTITY_ENDPOINT')
    header = os.environ.get('IDENTITY_HEADER')

    if not endpoint or not header:
        raise PurgeError('No managed identity is available to authenticate the purge.')

    params = {'resource': MANAGEMENT_RESOURCE, 'api-version': TOKEN_API_VERSION}
    client_id = settings.FRONT_DOOR.get('identity_client_id')

    # A user-assigned identity has to be named; otherwise the endpoint
    # uses the system-assigned identity.
    if client_id:
        params['client_id'] = client_id

    response = requests.get(
        endpoint,
        params=params,
        headers={'X-IDENTITY-HEADER': header},
        timeout=TIMEOUT
    )

    if response.status_code != 200:
        raise PurgeError(f'Could not get a managed identity token ({response.status_code}): {response.text}')

    return response.json()['access_token']
