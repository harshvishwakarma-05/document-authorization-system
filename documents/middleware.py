from django.core.cache import cache
from django.http import HttpResponse

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.limit = 100  # Number of requests allowed
        self.timeout = 60  # Time window in seconds

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def __call__(self, request):
        # Allow requests for static and media files without rate limiting
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return self.get_response(request)

        ip = self.get_client_ip(request)
        cache_key = f'ratelimit_{ip}'
        
        # Get the current request count for this IP
        request_count = cache.get(cache_key, 0)

        if request_count >= self.limit:
            return HttpResponse("Too Many Requests", status=429)

        # Increment the count and set the timeout if it's the first request
        if request_count == 0:
            cache.set(cache_key, 1, self.timeout)
        else:
            cache.incr(cache_key)

        response = self.get_response(request)
        return response
