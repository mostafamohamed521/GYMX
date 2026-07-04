import json
from datetime import date, timedelta, datetime, time
from calendar import monthrange, monthcalendar

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Avg, F
from django.db.models.functions import TruncHour, ExtractWeekDay
from django.utils import timezone

from .models import AttendanceRecord, AttendanceSession, AttendanceSettings
from apps.members.models import Member
from apps.memberships.models import MemberSubscription


# ── Helpers ────────────────────────────────────────────────
def _session_today():
    today = timezone.now().date()
    session, _ = AttendanceSession.objects.get_or_create(date=today, is_open=True)
    return session


def _do_checkin(member, method='manual', user=None):
    """Returns (record, error_str)"""
    settings = AttendanceSettings.get()
    today    = timezone.now().date()

    if settings.require_membership:
        if not MemberSubscription.objects.filter(member=member, status='active').exists():
            return None, f"{member.get_full_name()} has no active membership."

    if AttendanceRecord.objects.filter(member=member, date=today, check_out__isnull=True).exists():
        return None, f"{member.get_full_name()} is already checked in."

    now      = timezone.now()
    open_dt  = timezone.make_aware(datetime.combine(today, settings.gym_open_time))
    mins_late = int((now - open_dt).total_seconds() // 60)
    status   = 'late' if mins_late > settings.late_threshold_min else 'present'

    record = AttendanceRecord.objects.create(
        member=member, session=_session_today(),
        date=today, check_in=now,
        check_in_method=method, status=status,
        recorded_by=user,
    )
    return record, None


def _streak(member):
    today, streak, d = timezone.now().date(), 0, timezone.now().date()
    while streak <= 365:
        if AttendanceRecord.objects.filter(member=member, date=d).exists():
            streak += 1
            d -= timedelta(days=1)
        else:
            break
    return streak


def _peak_hour():
    try:
        r = (AttendanceRecord.objects
             .filter(check_in__isnull=False)
             .annotate(h=TruncHour('check_in'))
             .values('h').annotate(c=Count('id'))
             .order_by('-c').first())
        return r['h'].strftime('%H:00') if r and r['h'] else '—'
    except Exception:
        return '—'


# ── 1. Dashboard ───────────────────────────────────────────
@login_required
def dashboard(request):
    today    = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago= today - timedelta(days=30)

    today_qs = AttendanceRecord.objects.filter(date=today)
    inside   = today_qs.filter(check_out__isnull=True)

    total_month = AttendanceRecord.objects.filter(date__gte=month_ago).count()
    stats = {
        'inside_now':   inside.count(),
        'today_total':  today_qs.count(),
        'checked_out':  today_qs.filter(check_out__isnull=False).count(),
        'late_today':   today_qs.filter(status='late').count(),
        'this_week':    AttendanceRecord.objects.filter(date__gte=week_ago).count(),
        'this_month':   total_month,
        'avg_per_day':  round(total_month / 30, 1),
        'peak_hour':    _peak_hour(),
    }

    weekly = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        weekly.append({'label': d.strftime('%a'), 'count': AttendanceRecord.objects.filter(date=d).count()})

    inside_members = inside.select_related('member').order_by('-check_in')[:10]
    recent         = AttendanceRecord.objects.select_related('member').order_by('-check_in')[:8]

    return render(request, 'attendance/dashboard.html', {
        'stats': stats, 'weekly': weekly,
        'inside_members': inside_members, 'recent': recent,
        'today': today, 'now': timezone.now(),
    })


# ── 2. Live Check-In ───────────────────────────────────────
@login_required
def live_checkin(request):
    today = timezone.now().date()

    if request.method == 'POST':
        mid    = request.POST.get('member_id', '').strip()
        method = request.POST.get('method', 'manual')
        member = (Member.objects.filter(member_id=mid).first() or
                  Member.objects.filter(pk=mid if mid.isdigit() else 0).first())
        if not member:
            messages.error(request, f'Member "{mid}" not found.')
        else:
            rec, err = _do_checkin(member, method=method, user=request.user)
            if err:
                messages.warning(request, err)
            else:
                label = 'Late' if rec.status == 'late' else 'On time'
                messages.success(request, f'✓ {member.get_full_name()} checked in — {label}')
        return redirect('attendance:live_checkin')

    inside  = AttendanceRecord.objects.filter(date=today, check_out__isnull=True).select_related('member').order_by('-check_in')
    recent  = AttendanceRecord.objects.filter(date=today).select_related('member').order_by('-check_in')[:20]
    members = Member.objects.filter(status='active').order_by('first_name')

    return render(request, 'attendance/live_checkin.html', {
        'inside': inside, 'inside_count': inside.count(),
        'recent': recent, 'members': members,
        'today': today, 'now': timezone.now(),
    })


# ── 3. Live Check-Out ──────────────────────────────────────
@login_required
def live_checkout(request):
    today = timezone.now().date()

    if request.method == 'POST':
        rec = get_object_or_404(AttendanceRecord, pk=request.POST.get('record_id'))
        rec.do_checkout(method=request.POST.get('method', 'manual'), recorded_by=request.user)
        messages.success(request, f'✓ {rec.member.get_full_name()} checked out — {rec.duration_display}')
        return redirect('attendance:live_checkout')

    inside = AttendanceRecord.objects.filter(date=today, check_out__isnull=True).select_related('member').order_by('-check_in')
    return render(request, 'attendance/live_checkout.html', {
        'inside': inside, 'count': inside.count(),
        'today': today, 'now': timezone.now(),
    })


# ── 4. QR Scanner ──────────────────────────────────────────
@login_required
def qr_scanner(request):
    return render(request, 'attendance/qr_scanner.html')


# ── 5. Barcode Scanner ─────────────────────────────────────
@login_required
def barcode_scanner(request):
    return render(request, 'attendance/barcode_scanner.html')


# ── 6. Face Recognition ────────────────────────────────────
@login_required
def face_recognition(request):
    return render(request, 'attendance/face_recognition.html')


# ── 7. Today's Attendance ──────────────────────────────────
@login_required
def today_attendance(request):
    today   = timezone.now().date()
    records = AttendanceRecord.objects.filter(date=today).select_related('member').order_by('-check_in')

    q = request.GET.get('q', '')
    if q:
        records = records.filter(
            Q(member__first_name__icontains=q) | Q(member__last_name__icontains=q) | Q(member__member_id__icontains=q)
        )

    stats = {
        'total':   records.count(),
        'inside':  records.filter(check_out__isnull=True).count(),
        'left':    records.filter(check_out__isnull=False).count(),
        'late':    records.filter(status='late').count(),
        'on_time': records.filter(status='present').count(),
    }

    hourly = list(
        records.filter(check_in__isnull=False)
        .annotate(hour=TruncHour('check_in'))
        .values('hour').annotate(count=Count('id')).order_by('hour')
    )

    return render(request, 'attendance/today_attendance.html', {
        'records': records, 'stats': stats,
        'today': today, 'q': q, 'hourly': hourly,
    })


# ── 8. Attendance Calendar ─────────────────────────────────
@login_required
def att_calendar(request):
    today = timezone.now().date()
    year  = int(request.GET.get('year',  today.year))
    month = int(request.GET.get('month', today.month))

    _, days_in_month = monthrange(year, month)
    start = date(year, month, 1)
    end   = date(year, month, days_in_month)

    daily = (AttendanceRecord.objects
             .filter(date__gte=start, date__lte=end)
             .values('date').annotate(count=Count('id')))
    counts_map = {row['date']: row['count'] for row in daily}

    if month == 1:
        prev_y, prev_m = year - 1, 12
    else:
        prev_y, prev_m = year, month - 1
    if month == 12:
        next_y, next_m = year + 1, 1
    else:
        next_y, next_m = year, month + 1

    return render(request, 'attendance/attendance_calendar.html', {
        'year': year, 'month': month,
        'month_name': start.strftime('%B'),
        'cal_weeks': monthcalendar(year, month),
        'counts_map': counts_map,
        'today': today,
        'prev_year': prev_y, 'prev_month': prev_m,
        'next_year': next_y, 'next_month': next_m,
    })


# ── 9. Attendance History ──────────────────────────────────
@login_required
def att_history(request):
    records   = AttendanceRecord.objects.select_related('member').order_by('-date', '-check_in')
    q         = request.GET.get('q', '')
    date_from = request.GET.get('from', '')
    date_to   = request.GET.get('to', '')
    status_f  = request.GET.get('status', '')
    method_f  = request.GET.get('method', '')

    if q:
        records = records.filter(Q(member__first_name__icontains=q) | Q(member__last_name__icontains=q) | Q(member__member_id__icontains=q))
    if date_from:
        records = records.filter(date__gte=date_from)
    if date_to:
        records = records.filter(date__lte=date_to)
    if status_f:
        records = records.filter(status=status_f)
    if method_f:
        records = records.filter(check_in_method=method_f)

    total = records.count()
    return render(request, 'attendance/attendance_history.html', {
        'records': records[:200], 'total': total,
        'q': q, 'date_from': date_from, 'date_to': date_to,
        'status_f': status_f, 'method_f': method_f,
        'statuses': AttendanceRecord.Status.choices,
        'methods':  AttendanceRecord.CheckInMethod.choices,
    })


# ── 10. Member Attendance ──────────────────────────────────
@login_required
def member_attendance(request, pk):
    member    = get_object_or_404(Member, pk=pk)
    records   = AttendanceRecord.objects.filter(member=member).order_by('-date', '-check_in')
    today     = timezone.now().date()
    month_ago = today - timedelta(days=30)

    stats = {
        'total_visits': records.count(),
        'this_month':   records.filter(date__gte=month_ago).count(),
        'on_time':      records.filter(status='present').count(),
        'late':         records.filter(status='late').count(),
        'last_visit':   records.first(),
        'streak':       _streak(member),
    }

    monthly = []
    for i in range(5, -1, -1):
        d = today.replace(day=1) - timedelta(days=i * 30)
        monthly.append({'label': d.strftime('%b'), 'count': records.filter(date__year=d.year, date__month=d.month).count()})

    return render(request, 'attendance/member_attendance.html', {
        'member': member, 'records': records[:50],
        'stats': stats, 'monthly': monthly, 'today': today,
    })


# ── 11. Reports ────────────────────────────────────────────
@login_required
def att_reports(request):
    today     = timezone.now().date()
    date_from = request.GET.get('from', str(today - timedelta(days=30)))
    date_to   = request.GET.get('to',   str(today))

    records = AttendanceRecord.objects.filter(date__gte=date_from, date__lte=date_to).select_related('member')

    top_members = (records.values('member__first_name', 'member__last_name', 'member__member_id', 'member__pk')
                   .annotate(visits=Count('id')).order_by('-visits')[:10])

    daily_summary = (records.values('date')
                     .annotate(total=Count('id'), late=Count('id', filter=Q(status='late')))
                     .order_by('-date')[:30])

    method_stats = (records.values('check_in_method').annotate(count=Count('id')).order_by('-count'))

    try:
        d_from = date.fromisoformat(date_from)
        d_to   = date.fromisoformat(date_to)
        days   = max((d_to - d_from).days, 1)
    except Exception:
        days = 30

    total = records.count()
    stats = {
        'total':           total,
        'unique_members':  records.values('member').distinct().count(),
        'on_time':         records.filter(status='present').count(),
        'late':            records.filter(status='late').count(),
        'avg_per_day':     round(total / days, 1),
    }

    return render(request, 'attendance/reports.html', {
        'stats': stats, 'top_members': top_members,
        'daily_summary': daily_summary, 'method_stats': method_stats,
        'date_from': date_from, 'date_to': date_to, 'today': today,
    })


# ── 12. Late Members ───────────────────────────────────────
@login_required
def late_members(request):
    today  = timezone.now().date()
    date_f = request.GET.get('date', str(today))
    records = AttendanceRecord.objects.filter(date=date_f, status='late').select_related('member').order_by('-check_in')
    return render(request, 'attendance/late_members.html', {
        'records': records, 'date_f': date_f,
        'count': records.count(), 'today': today,
    })


# ── 13. Absent Members ─────────────────────────────────────
@login_required
def absent_members(request):
    today  = timezone.now().date()
    date_f = request.GET.get('date', str(today))

    attended_pks = AttendanceRecord.objects.filter(date=date_f).values_list('member_id', flat=True)
    absent = Member.objects.filter(status='active').exclude(pk__in=attended_pks).order_by('first_name')

    chronic = []
    for m in absent:
        streak, d = 0, today
        while True:
            if AttendanceRecord.objects.filter(member=m, date=d).exists():
                break
            streak += 1
            d -= timedelta(days=1)
            if streak > 30:
                break
        if streak >= 3:
            chronic.append({'member': m, 'days': streak})

    return render(request, 'attendance/absent_members.html', {
        'absent': absent, 'count': absent.count(),
        'chronic': chronic, 'date_f': date_f, 'today': today,
    })


# ── 14. Statistics ─────────────────────────────────────────
@login_required
def att_statistics(request):
    today     = timezone.now().date()
    month_ago = today - timedelta(days=30)
    year_ago  = today - timedelta(days=365)

    monthly = []
    for i in range(11, -1, -1):
        d = today.replace(day=1) - timedelta(days=i * 30)
        monthly.append({'label': d.strftime('%b %y'), 'count': AttendanceRecord.objects.filter(date__year=d.year, date__month=d.month).count()})

    weekday_data = (AttendanceRecord.objects.filter(date__gte=month_ago)
                    .annotate(wd=ExtractWeekDay('date')).values('wd')
                    .annotate(count=Count('id')).order_by('wd'))
    day_names  = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    wd_map     = {row['wd']: row['count'] for row in weekday_data}
    weekday_chart = [{'day': day_names[i], 'count': wd_map.get(i + 1, 0)} for i in range(7)]

    method_dist = (AttendanceRecord.objects.filter(date__gte=month_ago)
                   .values('check_in_method').annotate(count=Count('id')).order_by('-count'))

    total_month = AttendanceRecord.objects.filter(date__gte=month_ago).count()
    late_month  = AttendanceRecord.objects.filter(date__gte=month_ago, status='late').count()
    qr_month    = AttendanceRecord.objects.filter(date__gte=month_ago, check_in_method='qr').count()

    stats = {
        'total_all_time':   AttendanceRecord.objects.count(),
        'total_this_month': total_month,
        'total_this_year':  AttendanceRecord.objects.filter(date__gte=year_ago).count(),
        'unique_members':   AttendanceRecord.objects.values('member').distinct().count(),
        'avg_per_day':      round(total_month / 30, 1),
        'late_rate_pct':    round(late_month / max(total_month, 1) * 100, 1),
        'peak_hour':        _peak_hour(),
        'qr_usage_pct':     round(qr_month / max(total_month, 1) * 100, 1),
    }

    return render(request, 'attendance/statistics.html', {
        'stats': stats, 'monthly': monthly,
        'weekday_chart': weekday_chart, 'method_dist': method_dist,
        'today': today,
    })


# ── AJAX ───────────────────────────────────────────────────
@login_required
def ajax_checkin(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required'})
    data   = json.loads(request.body)
    mid    = data.get('member_id', '').strip()
    method = data.get('method', 'qr')
    member = (Member.objects.filter(member_id=mid).first() or
              Member.objects.filter(pk=mid if mid.isdigit() else 0).first())
    if not member:
        return JsonResponse({'ok': False, 'error': f'Member "{mid}" not found.'})
    rec, err = _do_checkin(member, method=method, user=request.user)
    if err:
        return JsonResponse({'ok': False, 'error': err})
    return JsonResponse({'ok': True, 'name': member.get_full_name(),
                         'id': member.member_id, 'status': rec.status,
                         'time': rec.check_in.strftime('%H:%M')})


@login_required
def ajax_checkout(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required'})
    data = json.loads(request.body)
    try:
        rec = AttendanceRecord.objects.select_related('member').get(pk=data.get('record_id'), check_out__isnull=True)
    except AttendanceRecord.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Record not found.'})
    rec.do_checkout(method=data.get('method', 'qr'), recorded_by=request.user)
    return JsonResponse({'ok': True, 'name': rec.member.get_full_name(), 'duration': rec.duration_display})


@login_required
def ajax_live_count(request):
    count = AttendanceRecord.objects.filter(date=timezone.now().date(), check_out__isnull=True).count()
    return JsonResponse({'count': count, 'time': timezone.now().strftime('%H:%M:%S')})
