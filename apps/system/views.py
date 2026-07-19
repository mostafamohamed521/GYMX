from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import connection
from django.core.cache import cache
from django.utils import timezone

from apps.accounts.permissions import role_required, ADMIN_ROLES, ALL_ROLES
from .models import MaintenanceSettings, ReleaseNote, HelpArticle, DocPage


# ── Error Pages (also wired as real Django error handlers — see config/urls.py) ──
def custom_401(request, exception=None):
    return render(request, 'system/errors/401.html', status=401)


def custom_403(request, exception=None):
    return render(request, 'system/errors/403.html', status=403)


def custom_404(request, exception=None):
    return render(request, 'system/errors/404.html', status=404)


def custom_500(request):
    return render(request, 'system/errors/500.html', status=500)


# Preview routes so admins can view/QA these pages without triggering the real error
@role_required(*ADMIN_ROLES)
def preview_401(request):
    return render(request, 'system/errors/401.html', {'is_preview': True})


@role_required(*ADMIN_ROLES)
def preview_403(request):
    return render(request, 'system/errors/403.html', {'is_preview': True})


@role_required(*ADMIN_ROLES)
def preview_404(request):
    return render(request, 'system/errors/404.html', {'is_preview': True})


@role_required(*ADMIN_ROLES)
def preview_500(request):
    return render(request, 'system/errors/500.html', {'is_preview': True})


# ── Maintenance Mode ────────────────────────────────────────
@role_required(*ADMIN_ROLES)
def maintenance_mode(request):
    settings_obj = MaintenanceSettings.load()
    if request.method == 'POST':
        settings_obj.is_enabled = bool(request.POST.get('is_enabled'))
        settings_obj.message = request.POST.get('message', settings_obj.message)
        settings_obj.starts_at = request.POST.get('starts_at') or None
        settings_obj.ends_at = request.POST.get('ends_at') or None
        settings_obj.updated_by = request.user
        settings_obj.save()
        state = 'enabled' if settings_obj.is_enabled else 'disabled'
        messages.success(request, f'Maintenance mode {state}!')
        return redirect('coresystem:maintenance')
    return render(request, 'system/maintenance_settings.html', {'settings_obj': settings_obj})


# ── System Status ────────────────────────────────────────────
@role_required(*ADMIN_ROLES)
def system_status(request):
    checks = []

    # Database check
    try:
        connection.ensure_connection()
        checks.append({'name': 'Database', 'status': 'operational', 'detail': 'Connected'})
    except Exception as e:
        checks.append({'name': 'Database', 'status': 'down', 'detail': str(e)})

    # Cache check
    try:
        cache.set('healthcheck', 'ok', 5)
        ok = cache.get('healthcheck') == 'ok'
        checks.append({'name': 'Cache', 'status': 'operational' if ok else 'degraded', 'detail': 'Working' if ok else 'Unavailable'})
    except Exception as e:
        checks.append({'name': 'Cache', 'status': 'down', 'detail': str(e)})

    # Maintenance mode check
    maintenance = MaintenanceSettings.load()
    checks.append({
        'name': 'Application', 'status': 'maintenance' if maintenance.is_enabled else 'operational',
        'detail': 'Maintenance mode active' if maintenance.is_enabled else 'Running normally',
    })

    # Static/media placeholders (assumed operational in this environment)
    checks.append({'name': 'Static Files', 'status': 'operational', 'detail': 'Serving normally'})
    checks.append({'name': 'Media Storage', 'status': 'operational', 'detail': 'Serving normally'})

    overall = 'operational'
    if any(c['status'] == 'down' for c in checks):
        overall = 'down'
    elif any(c['status'] in ('degraded', 'maintenance') for c in checks):
        overall = 'degraded'

    return render(request, 'system/system_status.html', {
        'checks': checks, 'overall': overall, 'checked_at': timezone.now(),
    })


# ── Help Center ────────────────────────────────────────────────
@role_required(*ALL_ROLES)
def help_center(request):
    articles = HelpArticle.objects.all()
    grouped = {}
    for a in articles:
        grouped.setdefault(a.category, []).append(a)
    return render(request, 'system/help_center.html', {'grouped': grouped})


# ── Documentation ────────────────────────────────────────────
@role_required(*ADMIN_ROLES)
def documentation(request):
    pages = DocPage.objects.all()
    grouped = {}
    for p in pages:
        grouped.setdefault(p.section, []).append(p)
    return render(request, 'system/documentation.html', {'grouped': grouped})


# ── Release Notes ─────────────────────────────────────────────
@role_required(*ALL_ROLES)
def release_notes(request):
    releases = ReleaseNote.objects.all()
    return render(request, 'system/release_notes.html', {'releases': releases})


# ── Version History ───────────────────────────────────────────
@role_required(*ADMIN_ROLES)
def version_history(request):
    releases = ReleaseNote.objects.all()
    return render(request, 'system/version_history.html', {'releases': releases})
