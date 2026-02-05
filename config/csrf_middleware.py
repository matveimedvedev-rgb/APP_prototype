"""
Custom middleware to handle Cloud Run dynamic domains for CSRF.
This middleware runs before CSRF middleware and automatically adds Cloud Run origins.
"""
from django.utils.deprecation import MiddlewareMixin


class CloudRunCsrfMiddleware(MiddlewareMixin):
    """
    Middleware to automatically add Cloud Run domains to CSRF_TRUSTED_ORIGINS.
    This should be placed before django.middleware.csrf.CsrfViewMiddleware.
    """
    def process_request(self, request):
        """Add Cloud Run origin to trusted origins before CSRF check."""
        # Get the origin from the request
        origin = request.META.get('HTTP_ORIGIN')
        if not origin:
            referer = request.META.get('HTTP_REFERER')
            if referer:
                from urllib.parse import urlparse
                parsed = urlparse(referer)
                origin = f"{parsed.scheme}://{parsed.netloc}"
        
        # If it's a Cloud Run domain, add it to trusted origins
        if origin and '.run.app' in origin:
            from django.conf import settings
            # Dynamically add to trusted origins for this request
            if origin not in settings.CSRF_TRUSTED_ORIGINS:
                # Convert to list if needed, then add
                trusted_origins = list(settings.CSRF_TRUSTED_ORIGINS)
                trusted_origins.append(origin)
                settings.CSRF_TRUSTED_ORIGINS = trusted_origins
        
        return None  # Continue processing

