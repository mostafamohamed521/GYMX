"""Shared utility helpers for the accounts app."""
from .models import LoginHistory, ActivityLog, Notification, UserSession


def get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR', '')


def log_login(request, user, status='success'):
    LoginHistory.objects.create(
        user=user,
        status=status,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
    )


def log_activity(request, user, action, description='', extra_data=None):
    ActivityLog.objects.create(
        user=user,
        action=action,
        description=description,
        ip_address=get_client_ip(request),
        extra_data=extra_data or {},
    )


def create_notification(user, type, title, message, link=''):
    Notification.objects.create(
        user=user, type=type, title=title,
        message=message, link=link,
    )


def track_session(request, user):
    """Register or update the active session for this user."""
    session_key = request.session.session_key or ''
    if not session_key:
        return
    UserSession.objects.update_or_create(
        session_key=session_key,
        defaults={
            'user': user,
            'ip_address': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
            'is_active': True,
        }
    )


def deactivate_session(session_key):
    UserSession.objects.filter(session_key=session_key).update(is_active=False)
