from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

from apps.accounts.permissions import role_required, FRONT_DESK_ROLES
from apps.accounts.models import Notification
from .models import (
    EmailTemplate, SMSTemplate, PushNotification,
    Announcement, ScheduledMessage,
)
from apps.members.models import Member
from apps.memberships.models import MemberSubscription
from apps.payments.models import Payment, Invoice
from apps.accounts.notifications import send_email, send_sms


@role_required(*FRONT_DESK_ROLES)
def payment_reminder_send(request, kind, pk):
    """Send a payment/invoice/expiry reminder to a member (email + SMS)."""
    if kind == 'payment':
        obj = get_object_or_404(Payment, pk=pk)
        member = obj.member
        subject = "GymX — Payment Reminder"
        body = f"Hi {member.get_full_name()}, this is a reminder about your pending payment of {obj.net_amount} EGP."
        redirect_to = 'notifications:payment_reminders'
    elif kind == 'invoice':
        obj = get_object_or_404(Invoice, pk=pk)
        member = obj.member
        subject = "GymX — Overdue Invoice Reminder"
        body = f"Hi {member.get_full_name()}, invoice for {obj.total} EGP was due on {obj.due_date}. Please settle it soon."
        redirect_to = 'notifications:payment_reminders'
    elif kind == 'expiry':
        obj = get_object_or_404(MemberSubscription, pk=pk)
        member = obj.member
        subject = "GymX — Membership Expiry Reminder"
        body = f"Hi {member.get_full_name()}, your membership ends on {obj.end_date}. Renew now to keep training!"
        redirect_to = 'notifications:expiry_alerts'
    else:
        messages.error(request, 'Unknown reminder type.')
        return redirect('notifications:payment_reminders')

    sent = False
    if member.email:
        sent = send_email(member.email, subject, f"<p>{body}</p>") or sent
    if getattr(member, 'phone', None):
        sent = send_sms(member.phone, body) or sent

    if sent:
        messages.success(request, f'Reminder sent to {member.get_full_name()}.')
    else:
        messages.warning(request, f'{member.get_full_name()} has no email or phone on file — reminder not sent.')

    return redirect(redirect_to)


# ── 1. Notification Center ─────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def notification_center(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()
    return render(request, 'notifications/notification_center.html', {
        'notifications': notifications, 'unread_count': unread_count,
    })


@role_required(*FRONT_DESK_ROLES)
def mark_read(request, pk):
    n = get_object_or_404(Notification, pk=pk, user=request.user)
    n.is_read = True
    n.save(update_fields=['is_read'])
    return redirect('notifications:center')


@role_required(*FRONT_DESK_ROLES)
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, 'All notifications marked as read.')
    return redirect('notifications:center')


# ── 2. Email Templates ─────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def email_templates(request):
    templates = EmailTemplate.objects.order_by('name')
    return render(request, 'notifications/email_templates.html', {'templates': templates})


@role_required(*FRONT_DESK_ROLES)
def email_template_new(request):
    if request.method == 'POST':
        EmailTemplate.objects.create(
            name=request.POST.get('name'), purpose=request.POST.get('purpose','custom'),
            subject=request.POST.get('subject'), body=request.POST.get('body'),
        )
        messages.success(request, 'Email template created!')
        return redirect('notifications:email_templates')
    return render(request, 'notifications/email_template_form.html', {
        'purposes': EmailTemplate.Purpose.choices,
    })


# ── 3. SMS Templates ────────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def sms_templates(request):
    templates = SMSTemplate.objects.order_by('name')
    return render(request, 'notifications/sms_templates.html', {'templates': templates})


@role_required(*FRONT_DESK_ROLES)
def sms_template_new(request):
    if request.method == 'POST':
        SMSTemplate.objects.create(
            name=request.POST.get('name'), purpose=request.POST.get('purpose','custom'),
            body=request.POST.get('body'),
        )
        messages.success(request, 'SMS template created!')
        return redirect('notifications:sms_templates')
    return render(request, 'notifications/sms_template_form.html', {
        'purposes': SMSTemplate.Purpose.choices,
    })


# ── 4. Push Notifications ──────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def push_notifications(request):
    pushes = PushNotification.objects.order_by('-created_at')
    return render(request, 'notifications/push_notifications.html', {'pushes': pushes})


@role_required(*FRONT_DESK_ROLES)
def push_new(request):
    if request.method == 'POST':
        status = request.POST.get('status', 'draft')
        push = PushNotification.objects.create(
            title=request.POST.get('title'), message=request.POST.get('message'),
            target_audience=request.POST.get('target_audience','All members'),
            status=status, scheduled_at=request.POST.get('scheduled_at') or None,
            created_by=request.user,
        )
        if status == 'sent':
            push.sent_at = timezone.now()
            push.recipients_count = Member.objects.filter(status='active').count()
            push.save()
        messages.success(request, 'Push notification created!')
        return redirect('notifications:push')
    return render(request, 'notifications/push_form.html', {
        'statuses': PushNotification.Status.choices,
    })


# ── 5. Announcement Center ─────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def announcement_center(request):
    announcements = Announcement.objects.order_by('-is_pinned','-created_at')
    return render(request, 'notifications/announcement_center.html', {'announcements': announcements})


@role_required(*FRONT_DESK_ROLES)
def announcement_new(request):
    if request.method == 'POST':
        Announcement.objects.create(
            title=request.POST.get('title'), body=request.POST.get('body'),
            priority=request.POST.get('priority','normal'),
            is_pinned=bool(request.POST.get('is_pinned')),
            ends_at=request.POST.get('ends_at') or None,
            created_by=request.user,
        )
        messages.success(request, 'Announcement published!')
        return redirect('notifications:announcements')
    return render(request, 'notifications/announcement_form.html', {
        'priorities': Announcement.Priority.choices,
    })


# ── 6. Birthday Messages ───────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def birthday_messages(request):
    today = date.today()
    upcoming_window = today + timedelta(days=7)

    members = Member.objects.filter(status='active', birth_date__isnull=False)
    todays_birthdays = [m for m in members if m.birth_date.month == today.month and m.birth_date.day == today.day]
    upcoming_birthdays = []
    for m in members:
        this_year_bday = m.birth_date.replace(year=today.year)
        if this_year_bday < today:
            this_year_bday = this_year_bday.replace(year=today.year + 1)
        if today < this_year_bday <= upcoming_window:
            upcoming_birthdays.append((m, this_year_bday))
    upcoming_birthdays.sort(key=lambda x: x[1])

    return render(request, 'notifications/birthday_messages.html', {
        'todays_birthdays': todays_birthdays, 'upcoming_birthdays': upcoming_birthdays,
    })


@role_required(*FRONT_DESK_ROLES)
def birthday_send(request, pk):
    member = get_object_or_404(Member, pk=pk)
    messages.success(request, f'🎂 Birthday message sent to {member.get_full_name()}!')
    return redirect('notifications:birthdays')


# ── 7. Membership Expiry Alerts ────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def expiry_alerts(request):
    today = date.today()
    window = today + timedelta(days=14)

    expiring = MemberSubscription.objects.filter(
        status='active', end_date__gte=today, end_date__lte=window
    ).select_related('member', 'plan').order_by('end_date')

    expired = MemberSubscription.objects.filter(
        status='active', end_date__lt=today
    ).select_related('member', 'plan').order_by('-end_date')[:20]

    return render(request, 'notifications/expiry_alerts.html', {
        'expiring': expiring, 'expired': expired,
    })


# ── 8. Payment Reminders ───────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def payment_reminders(request):
    pending_payments = Payment.objects.filter(status='pending').select_related('member').order_by('payment_date')
    overdue_invoices = Invoice.objects.filter(status='overdue').select_related('member').order_by('due_date')

    return render(request, 'notifications/payment_reminders.html', {
        'pending_payments': pending_payments, 'overdue_invoices': overdue_invoices,
    })


# ── 9. Scheduled Messages ──────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def scheduled_messages(request):
    scheduled = ScheduledMessage.objects.order_by('scheduled_for')
    return render(request, 'notifications/scheduled_messages.html', {'scheduled': scheduled})


@role_required(*FRONT_DESK_ROLES)
def scheduled_new(request):
    if request.method == 'POST':
        ScheduledMessage.objects.create(
            name=request.POST.get('name'), channel=request.POST.get('channel','email'),
            target_audience=request.POST.get('target_audience','All members'),
            message=request.POST.get('message'), scheduled_for=request.POST.get('scheduled_for'),
            created_by=request.user,
        )
        messages.success(request, 'Message scheduled!')
        return redirect('notifications:scheduled')
    return render(request, 'notifications/scheduled_form.html', {
        'channels': ScheduledMessage.Channel.choices,
    })
