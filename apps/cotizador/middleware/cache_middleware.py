from django.core.cache import cache
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
import hashlib
import json

class QueryCacheMiddleware(MiddlewareMixin):
    """
    Middleware to cache expensive database queries.
    """
    def process_request(self, request):
        # Only cache GET requests
        if request.method != 'GET':
            return None

        # Generate cache key based on full URL and query parameters
        cache_key = self._generate_cache_key(request)
        cached_response = cache.get(cache_key)

        if cached_response is not None:
            return cached_response

        return None

    def process_response(self, request, response):
        if request.method != 'GET':
            return response

        # Only cache 200 OK responses
        if response.status_code != 200:
            return response

        # Generate cache key
        cache_key = self._generate_cache_key(request)

        # Cache the response for CACHE_TTL seconds
        cache.set(cache_key, response, settings.CACHE_TTL)

        return response

    def _generate_cache_key(self, request):
        """Generate a unique cache key based on the request."""
        # Get the full path including query parameters
        full_path = request.get_full_path()
        
        # Add user info to make cache user-specific if needed
        if request.user.is_authenticated:
            user_id = str(request.user.id)
        else:
            user_id = 'anonymous'

        # Create a unique key
        key_parts = [
            settings.CACHE_KEY_PREFIX,
            full_path,
            user_id,
        ]

        # Add request body for POST requests
        if request.method == 'POST':
            try:
                body = json.loads(request.body)
                key_parts.append(json.dumps(body, sort_keys=True))
            except:
                pass

        # Create a hash of all parts
        key = hashlib.md5(''.join(key_parts).encode()).hexdigest()
        
        return f'query_cache:{key}'
