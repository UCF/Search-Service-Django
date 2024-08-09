import logging
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework import status

CACHE_KEY = 'cached_jobs'
CACHE_TIMEOUT = 604800  # 1 week

def get_cached_jobs():
    # Retrieve cached job listings if available.
    return cache.get(CACHE_KEY)

def set_cached_jobs(jobs_response_data):
    # Cache the job listings data and handle errors if caching fails.
    if jobs_response_data['jobPostings']:
        try:
            logging.info('cache was set')
            cache.set(CACHE_KEY, jobs_response_data, timeout=CACHE_TIMEOUT)
        except Exception as e:
            logging.error(f"An error occurred while caching the jobs: {str(e)}")
            return Response({"error": "An error occurred while caching the jobs", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({"error": "No jobs found"}, status=status.HTTP_404_NOT_FOUND)
