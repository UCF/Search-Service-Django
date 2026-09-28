from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.utils.cache import patch_cache_control


class CacheControlMiddleware:
    """
    Sets Cache-Control headers for Front Door from CACHE_CONTROL_TTLS, a
    map of URL path prefixes to seconds where the longest matching prefix
    wins. A successful anonymous GET gets `public, max-age=<seconds>`.
    Anything else on a matched path, or on a prefix mapped to 0, gets
    `private, no-store`. Responses that already set Cache-Control, like
    the admin's, keep their own.

    Removed from the middleware chain unless CACHE_CONTROL_ENABLED is
    set, so the VMs, where Varnish sets the TTLs, are unaffected.
    """
    def __init__(self, get_response):
        if not settings.CACHE_CONTROL_ENABLED:
            raise MiddlewareNotUsed

        self.get_response = get_response
        self.ttls = sorted(
            settings.CACHE_CONTROL_TTLS.items(),
            key=lambda item: len(item[0]),
            reverse=True
        )

    def __call__(self, request):
        response = self.get_response(request)

        if response.has_header('Cache-Control'):
            return response

        ttl = self.ttl_for(request.path)

        if ttl is None:
            return response

        if ttl > 0 and self.is_shareable(request, response):
            patch_cache_control(response, public=True, max_age=ttl)
        else:
            patch_cache_control(response, private=True, no_store=True)

        return response

    def ttl_for(self, path):
        for prefix, ttl in self.ttls:
            if path.startswith(prefix):
                return ttl

        return None

    def is_shareable(self, request, response):
        """
        Whether the response is the same for every visitor. An API key
        or a session makes it specific to one, and so does a cookie.
        """
        user = getattr(request, 'user', None)

        return (
            request.method in ('GET', 'HEAD')
            and response.status_code == 200
            and not response.cookies
            and not (user and user.is_authenticated)
        )
