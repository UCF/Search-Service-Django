import logging
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework import status

CACHE_KEY = 'cached_jobs'
CACHE_TIMEOUT = 604800  # 1 week

def get_cached_jobs():
    # Retrieve cached job listings if available.
    return cache.get(CACHE_KEY)

def set_cached_jobs(jobs_response_data) -> list:
    # Cache the job listings data and handle errors if caching fails.
    if jobs_response_data:
        try:
            logging.info('cache was set')
            cache.set(CACHE_KEY, jobs_response_data, timeout=CACHE_TIMEOUT)
            return jobs_response_data
        except Exception as e:
            logging.error(f"An error occurred while caching the jobs: {str(e)}")
            raise e
    else:
        return []
