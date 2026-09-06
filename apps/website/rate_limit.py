"""
Simple IP-based rate limiting for public, unauthenticated forms.

Uses Django's cache framework (works out of the box with the default
LocMemCache, no Redis/Memcached needed) to stop basic spam scripts from
flooding the CRM with fake leads, spamming the contact form, or filling
disk space with job-application uploads. This is not meant to stop a
determined attacker (they can rotate IPs) — it's a low-cost first line
of defense appropriate for a single-process deployment.
"""
from functools import wraps
from django.core.cache import cache
from django.contrib import messages
from django.shortcuts import redirect


def get_client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


def rate_limit_post(key_prefix, max_attempts=5, window_seconds=3600, redirect_to=None):
    """
    Decorator for a view: on POST requests, allows at most `max_attempts`
    submissions per client IP within `window_seconds`. GET requests always
    pass through untouched. On the request that exceeds the limit, shows an
    error message and redirects back (to `redirect_to`, or the same URL by
    default) instead of processing the form.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if request.method == 'POST':
                ip = get_client_ip(request)
                cache_key = f'ratelimit:{key_prefix}:{ip}'
                attempts = cache.get(cache_key, 0)
                if attempts >= max_attempts:
                    messages.error(
                        request,
                        "You've submitted this form too many times recently. Please try again later."
                    )
                    target = redirect_to or request.path
                    return redirect(target)
                cache.set(cache_key, attempts + 1, timeout=window_seconds)
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator
