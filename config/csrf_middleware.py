"""
Custom CSRF middleware to handle Cloud Run dynamic domains.
This automatically trusts Cloud Run *.run.app domains for CSRF.
"""
from django.middleware.csrf import CsrfViewMiddleware
from django.utils.deprecation import MiddlewareMixin


class CloudRunCsrfMiddleware(MiddlewareMixin, CsrfViewMiddleware):
    """
    Extends Django's CSrfViewMiddleware to automatically trust Cloud Run domains.
    """
    def process_view(self, request, callback, callback_args, callback_kwargs):
        """Override to add Cloud Run origin to trusted origins."""
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
            # Create a mutable copy if needed
            if origin not in settings.CSRF_TRUSTED_ORIGINS:
                # Use a thread-safe approach
                import threading
                if not hasattr(settings, '_csrf_trusted_origins_lock'):
                    settings._csrf_trusted_origins_lock = threading.Lock()
                
                with settings._csrf_trusted_origins_lock:
                    if origin not in settings.CSRF_TRUSTED_ORIGINS:
                        settings.CSRF_TRUSTED_ORIGINS = list(settings.CSRF_TRUSTED_ORIGINS) + [origin]
        
        # Call parent middleware
        return super().process_view(request, callback, callback_args, callback_kwargs)

