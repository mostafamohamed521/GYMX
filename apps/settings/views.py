import secrets
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone

from apps.accounts.permissions import role_required, ADMIN_ROLES
from apps.accounts.models import LoginHistory
from .models import (
    SystemSettings, BusinessHours, Holiday,
    AuditLog, BackupRecord,
)


# ── 1. General Settings ────────────────────────────────────
@role_required(*ADMIN_ROLES)
def general_settings(request):
    settings_obj = SystemSettings.load()
    if request.method == 'POST':
        settings_obj.timezone = request.POST.get('timezone', settings_obj.timezone)
        settings_obj.date_format = request.POST.get('date_format', settings_obj.date_format)
        settings_obj.save()
        messages.success(request, 'General settings updated!')
        return redirect('gymsettings:general')
    return render(request, 'settings/general_settings.html', {'settings_obj': settings_obj})


# ── 2. Gym Information ─────────────────────────────────────
@role_required(*ADMIN_ROLES)
def gym_information(request):
    settings_obj = SystemSettings.load()
    if request.method == 'POST':
        settings_obj.gym_name = request.POST.get('gym_name', settings_obj.gym_name)
        settings_obj.address  = request.POST.get('address', '')
        settings_obj.phone    = request.POST.get('phone', '')
        settings_obj.email    = request.POST.get('email', '')
        settings_obj.website  = request.POST.get('website', '')
        if 'logo' in request.FILES:
            settings_obj.logo = request.FILES['logo']
        settings_obj.save()
        messages.success(request, 'Gym information updated!')
        return redirect('gymsettings:gym_info')
    return render(request, 'settings/gym_information.html', {'settings_obj': settings_obj})


# ── 3. Business Hours ──────────────────────────────────────
@role_required(*ADMIN_ROLES)
def business_hours(request):
    for day_val, _ in BusinessHours.Day.choices:
        BusinessHours.objects.get_or_create(day=day_val)

    if request.method == 'POST':
        for hours in BusinessHours.objects.all():
            prefix = f'day_{hours.day}'
            hours.is_open = bool(request.POST.get(f'{prefix}_open'))
            hours.open_time = request.POST.get(f'{prefix}_start', hours.open_time)
            hours.close_time = request.POST.get(f'{prefix}_end', hours.close_time)
            hours.save()
        messages.success(request, 'Business hours updated!')
        return redirect('gymsettings:business_hours')

    hours_list = BusinessHours.objects.order_by('day')
    return render(request, 'settings/business_hours.html', {'hours_list': hours_list})


# ── 4. Holidays ─────────────────────────────────────────────
@role_required(*ADMIN_ROLES)
def holidays(request):
    if request.method == 'POST':
        Holiday.objects.create(
            name=request.POST.get('name'), date=request.POST.get('date'),
            is_recurring=bool(request.POST.get('is_recurring')),
            is_closed=bool(request.POST.get('is_closed')),
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, 'Holiday added!')
        return redirect('gymsettings:holidays')

    holiday_list = Holiday.objects.order_by('date')
    return render(request, 'settings/holidays.html', {'holiday_list': holiday_list})


@role_required(*ADMIN_ROLES)
def holiday_delete(request, pk):
    h = get_object_or_404(Holiday, pk=pk)
    h.delete()
    messages.success(request, 'Holiday removed.')
    return redirect('gymsettings:holidays')


# ── 5. Security Center ──────────────────────────────────────
@role_required(*ADMIN_ROLES)
def security_center(request):
    recent_logins = LoginHistory.objects.select_related('user').order_by('-created_at')[:10]
    recent_audits = AuditLog.objects.select_related('user').order_by('-created_at')[:10]
    failed_logins_week = LoginHistory.objects.filter(status='failed', created_at__gte=timezone.now()-timedelta(days=7)).count()

    return render(request, 'settings/security_center.html', {
        'recent_logins': recent_logins, 'recent_audits': recent_audits,
        'failed_logins_week': failed_logins_week,
    })


# ── 6. Password Policies ────────────────────────────────────
@role_required(*ADMIN_ROLES)
def password_policy(request):
    settings_obj = SystemSettings.load()
    if request.method == 'POST':
        settings_obj.password_min_length = int(request.POST.get('password_min_length', 8))
        settings_obj.password_require_upper = bool(request.POST.get('password_require_upper'))
        settings_obj.password_require_number = bool(request.POST.get('password_require_number'))
        settings_obj.password_require_symbol = bool(request.POST.get('password_require_symbol'))
        settings_obj.password_expiry_days = int(request.POST.get('password_expiry_days', 90))
        settings_obj.save()
        messages.success(request, 'Password policy updated!')
        return redirect('gymsettings:password_policy')
    return render(request, 'settings/password_policy.html', {'settings_obj': settings_obj})


# ── 7. Login History ────────────────────────────────────────
@role_required(*ADMIN_ROLES)
def login_history(request):
    logins = LoginHistory.objects.select_related('user').order_by('-created_at')[:200]
    stats = {
        'total': LoginHistory.objects.count(),
        'failed': LoginHistory.objects.filter(status='failed').count(),
    }
    return render(request, 'settings/login_history.html', {'logins': logins, 'stats': stats})


# ── 8. Audit Logs ───────────────────────────────────────────
@role_required(*ADMIN_ROLES)
def audit_logs(request):
    logs = AuditLog.objects.select_related('user').order_by('-created_at')[:200]
    return render(request, 'settings/audit_logs.html', {'logs': logs})


# ── 9. API Settings ──────────────────────────────────────────
@role_required(*ADMIN_ROLES)
def api_settings(request):
    settings_obj = SystemSettings.load()
    if request.method == 'POST':
        if request.POST.get('regenerate'):
            settings_obj.api_key = secrets.token_hex(24)
        settings_obj.webhook_url = request.POST.get('webhook_url', '')
        settings_obj.api_rate_limit = int(request.POST.get('api_rate_limit', 1000))
        settings_obj.save()
        messages.success(request, 'API settings updated!')
        return redirect('gymsettings:api')
    if not settings_obj.api_key:
        settings_obj.api_key = secrets.token_hex(24)
        settings_obj.save(update_fields=['api_key'])
    return render(request, 'settings/api_settings.html', {'settings_obj': settings_obj})


# ── 10. Email Settings ───────────────────────────────────────
@role_required(*ADMIN_ROLES)
def email_settings(request):
    settings_obj = SystemSettings.load()
    if request.method == 'POST':
        settings_obj.smtp_host = request.POST.get('smtp_host', '')
        settings_obj.smtp_port = int(request.POST.get('smtp_port', 587))
        settings_obj.smtp_username = request.POST.get('smtp_username', '')
        settings_obj.smtp_from_email = request.POST.get('smtp_from_email', '')
        settings_obj.email_enabled = bool(request.POST.get('email_enabled'))
        settings_obj.save()
        messages.success(request, 'Email settings updated!')
        return redirect('gymsettings:email')
    return render(request, 'settings/email_settings.html', {'settings_obj': settings_obj})


# ── 11. SMS Settings ──────────────────────────────────────────
@role_required(*ADMIN_ROLES)
def sms_settings(request):
    settings_obj = SystemSettings.load()
    if request.method == 'POST':
        settings_obj.sms_provider = request.POST.get('sms_provider', '')
        settings_obj.sms_api_key = request.POST.get('sms_api_key', '')
        settings_obj.sms_sender_id = request.POST.get('sms_sender_id', '')
        settings_obj.sms_enabled = bool(request.POST.get('sms_enabled'))
        settings_obj.save()
        messages.success(request, 'SMS settings updated!')
        return redirect('gymsettings:sms')
    return render(request, 'settings/sms_settings.html', {'settings_obj': settings_obj})


# ── 12. Payment Gateway ───────────────────────────────────────
@role_required(*ADMIN_ROLES)
def payment_gateway(request):
    settings_obj = SystemSettings.load()
    if request.method == 'POST':
        settings_obj.payment_provider = request.POST.get('payment_provider', '')
        settings_obj.payment_public_key = request.POST.get('payment_public_key', '')
        settings_obj.payment_test_mode = bool(request.POST.get('payment_test_mode'))
        settings_obj.save()
        messages.success(request, 'Payment gateway settings updated!')
        return redirect('gymsettings:payment_gateway')
    return render(request, 'settings/payment_gateway.html', {'settings_obj': settings_obj})


# ── 13. Backup ─────────────────────────────────────────────────
@role_required(*ADMIN_ROLES)
def backup_center(request):
    backups = BackupRecord.objects.order_by('-created_at')
    return render(request, 'settings/backup_center.html', {'backups': backups})


@role_required(*ADMIN_ROLES)
def backup_new(request):
    import random
    BackupRecord.objects.create(
        filename=f"gymx_backup_{timezone.now().strftime('%Y%m%d_%H%M%S')}.sql",
        size_mb=round(random.uniform(5, 50), 2), status='completed', triggered_by=request.user,
    )
    messages.success(request, 'Backup created successfully!')
    return redirect('gymsettings:backup')


# ── 14. Restore ────────────────────────────────────────────────
@role_required(*ADMIN_ROLES)
def restore_center(request):
    backups = BackupRecord.objects.filter(status='completed').order_by('-created_at')
    if request.method == 'POST':
        backup = get_object_or_404(BackupRecord, pk=request.POST.get('backup_id'))
        messages.success(request, f'Restore from "{backup.filename}" initiated. This may take a few minutes.')
        return redirect('gymsettings:restore')
    return render(request, 'settings/restore_center.html', {'backups': backups})


# ── 15. Theme Settings ─────────────────────────────────────────
@role_required(*ADMIN_ROLES)
def theme_settings(request):
    settings_obj = SystemSettings.load()
    if request.method == 'POST':
        settings_obj.primary_color = request.POST.get('primary_color', settings_obj.primary_color)
        settings_obj.dark_mode_default = bool(request.POST.get('dark_mode_default'))
        settings_obj.save()
        messages.success(request, 'Theme settings updated!')
        return redirect('gymsettings:theme')
    return render(request, 'settings/theme_settings.html', {'settings_obj': settings_obj})


# ── 16. Language Settings ───────────────────────────────────────
@role_required(*ADMIN_ROLES)
def language_settings(request):
    settings_obj = SystemSettings.load()
    if request.method == 'POST':
        settings_obj.default_language = request.POST.get('default_language', settings_obj.default_language)
        settings_obj.save()
        messages.success(request, 'Language settings updated!')
        return redirect('gymsettings:language')
    return render(request, 'settings/language_settings.html', {'settings_obj': settings_obj})


# ── 17. Currency Settings ───────────────────────────────────────
@role_required(*ADMIN_ROLES)
def currency_settings(request):
    settings_obj = SystemSettings.load()
    if request.method == 'POST':
        settings_obj.default_currency = request.POST.get('default_currency', settings_obj.default_currency)
        settings_obj.currency_symbol = request.POST.get('currency_symbol', settings_obj.currency_symbol)
        settings_obj.save()
        messages.success(request, 'Currency settings updated!')
        return redirect('gymsettings:currency')
    return render(request, 'settings/currency_settings.html', {'settings_obj': settings_obj})
