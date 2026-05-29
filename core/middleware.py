"""
Security middleware for Nova Capital Group
"""
import time
import logging
from django.http import HttpResponseForbidden, JsonResponse
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    """Add security headers to all responses"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://s3.tradingview.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https: blob:; "
            "connect-src 'self' wss: https://api.coingecko.com https://query1.finance.yahoo.com; "
            "frame-src 'self' https://s.tradingview.com; "
        )
        response['Content-Security-Policy'] = csp
        
        return response


class RateLimitMiddleware:
    """Rate limiting middleware"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Sensitive endpoints and their limits (requests per minute)
        self.rate_limits = {
            '/accounts/login/': (10, 60),       # 10 per minute
            '/accounts/signup/': (5, 60),        # 5 per minute
            '/accounts/password/reset/': (5, 60), # 5 per minute
            '/api/': (60, 60),                   # 60 per minute for API
        }
    
    def __call__(self, request):
        # Check rate limits for sensitive endpoints
        for endpoint, (limit, window) in self.rate_limits.items():
            if request.path.startswith(endpoint):
                ip = self._get_client_ip(request)
                cache_key = f'rate_limit:{ip}:{endpoint}'
                
                requests = cache.get(cache_key, 0)
                if requests >= limit:
                    logger.warning(f"Rate limit exceeded for IP {ip} on {endpoint}")
                    if request.path.startswith('/api/'):
                        return JsonResponse({'error': 'Too many requests'}, status=429)
                    return HttpResponseForbidden('Too many requests. Please try again later.')
                
                cache.set(cache_key, requests + 1, window)
                break
        
        return self.get_response(request)
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')
