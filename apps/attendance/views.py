import json
from datetime import date, timedelta, datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Avg, F
from django.db.models.functions import TruncDate, TruncHour
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import AttendanceRecord, AttendanceSession, AttendanceSettings
from apps.members.models import Member
from apps.memberships.models import MemberSubscription


# ── Helpers ────────────────────────────────────────────────
def _get_or_create_session():
    today   = timezone.now().date()
    session = AttendanceSession.objects.filter(date=today, is_open=True).first()
    if not session:
        session = AttendanceSession.objects.create(date=today, is_open=True)
    return session


def _checkin_member(member, method='manual', user=None):
    """
    Check in a member. Returns (record, error_msg).
    """
    settings = AttendanceSettings.get()
    today    = timezone.now().date()

    # Check active membership
    if settings.require_membership:
        has_active = MemberSubscription.objects.filter(
            member=member, status='active'
        ).exists()
        if not has_active:
            return None, f"{member.get_full_name()} has no active membership."

    # Already checked in today?
    existing = AttendanceRecord.objects.filter(
        member=member, date=today, check_out__isnull=True
    ).first()
    if existing:
        return None, f"{member.get_full_name()} is already checked in."

    # Determine status (late?)
    now      = timezone.now()
    open_dt  = datetime.combine(today, settings.gym_open_time)
    open_dt  = timezone.make_aware(open_dt) if timezone.is_naive(open_dt) else open_dt
    late_min = settings.late_threshold_min
    status   = 'late' if (now - open_dt).seconds // 60 > late_min else 'present'

    session = _get_or_create_session()
    record  = AttendanceRecord.objects.create(
        member          = member,
        session         = session,
        date            = today,
        check_in        = now,
        check_in_method = method,
        status          = status,
        recorded_by     = user,
    )
    return record, None


# ── 1. Live Check-In ───────────────────────────────────────
@login_required
def live_checkin(request):
    today   = timezone.now().date()
    session = _get_or_create_session()

    if request.method == 'POST':
        member_id = request.POST.get('member_id', '').strip()
        method    = request.POST.get('method', 'manual')

        # Resolve member by member_id code or pk
        member = (
            Member.objects.filter(member_id=member_id).first() or
            Member.objects.filter(pk=member_id).first()
        )
        if not member:
            messages.error(request, f'Member "{member_id}" not found.')
        else:
            record, err = _checkin_member(member, method=method, user=request.user)
            if err:
                messages.warning(request, err)
            else:
                messages.success(
                    request,
                    f'✓ {member.get_full_name()} checked in successfully! '
                    f'({"Late" if record.status == "late" else "On time"})'
                )
        return redirect('attendance:live_checkin')

    # Today's checked-in members (still inside)
    inside = AttendanceRecord.objects.filter(
        date=today, check_out__isnull=True
    ).select_related('member').order_by('-check_in')

    recent = AttendanceRecord.objects.filter(
        date=today
    ).select_related('member').order_by('-check_in')[:20]

    members = Member.objects.filter(status='active').order_by('first_name')

    return render(request, 'attendance/live_checkin.html', {
        'session':    session,
        'inside':     inside,
        'inside_count': inside.count(),
        'recent':     recent,
        'members':    members,
        'today':      today,
        'now':        timezone.now(),
    })


# ── 2. Live Check-Out ──────────────────────────────────────
@login_required
def live_checkout(request):
    today = timezone.now().date()

    if request.method == 'POST':
        record_pk = request.POST.get('record_id')
        method    = request.POST.get('method', 'manual')
        record    = get_object_or_404(AttendanceRecord, pk=record_pk)
        record.do_checkout(method=method, recorded_by=request.user)
        messages.success(
            request,
            f'✓ {record.member.get_full_name()} checked out. '
            f'Duration: {record.duration_display}'
        )
        return redirect('attendance:live_checkout')

    inside = AttendanceRecord.objects.filter(
        date=today, check_out__isnull=True
    ).select_related('member').order_by('-check_in')

    return render(request, 'attendance/live_checkout.html', {
        'inside': inside,
        'count':  inside.count(),
        'today':  today,
        'now':    timezone.now(),
    })


# ── 3. QR Scanner ──────────────────────────────────────────
@login_required
def qr_scanner(request):
    return render(request, 'attendance/qr_scanner.html')


# ── 4. Barcode Scanner ─────────────────────────────────────
@login_required
def barcode_scanner(request):
    return render(request, 'attendance/barcode_scanner.html')


# ── 5. Face Recognition (Future) ───────────────────────────
@login_required
def face_recognition(request):
    return render(request, 'attendance/face_recognition.html')


# ── 6. Today's Attendance ──────────────────────────────────
@login_required
def today_attendance(request):
    today   = timezone.now().date()
    records = AttendanceRecord.objects.filter(
        date=today
    ).select_related('member').order_by('-check_in')

    q = request.GET.get('q', '')
    if q:
        records = records.filter(
            Q(member__first_name__icontains=q) |
            Q(member__last_name__icontains=q)  |
            Q(member__member_id__icontains=q)
        )

    stats = {
        'total':    records.count(),
        'inside':   records.filter(check_out__isnull=True).count(),
        'left':     records.filter(check_out__isnull=False).count(),
        'late':     records.filter(status='late').count(),
        'on_time':  records.filter(status='present').count(),
    }

    # Hourly breakdown
    hourly = (
        records.filter(check_in__isnull=False)
        .annotate(hour=TruncHour('check_in'))
        .values('hour')
        .annotate(count=Count('id'))
        .order_by('hour')
    )

    return render(request, 'attendance/today_attendance.html', {
        'records': records,
        'stats':   stats,
        'today':   today,
        'q':       q,
        'hourly':  list(hourly),
    })


# ── 7. Attendance Calendar ─────────────────────────────────
@login_required
def attendance_calendar(request):
    today    = timezone.now().date()
    year     = int(request.GET.get('year',  today.year))
    month    = int(request.GET.get('month', today.month))

    # Daily counts for the month
    from calendar import monthrange, monthcalendar
    _, days_in_month = monthrange(year, month)
    start = date(year, month, 1)
    end   = date(year, month, days_in_month)

    daily_counts = (
        AttendanceRecord.objects
        .filter(date__gte=start, date__lte=end)
        .values('date')
        .annotate(count=Count('id'))
    )
    counts_map = {row['date']: row['count'] for row in daily_counts}

    # Build calendar grid
    cal_weeks = monthcalendar(year, month)

    # Prev / next navigation
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1
    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1

    return render(request, 'attendance/attendance_calendar.html', {
        'year': year, 'month': month,
        'month_name': start.strftime('%B'),
        'cal_weeks':  cal_weeks,
        'counts_map': counts_map,
        'today':      today,
        'prev_year': prev_year, 'prev_month': prev_month,
        'next_year': next_year, 'next_month': next_month,
    })


# ── 8. Attendance History ──────────────────────────────────
@login_required
def attendance_history(request):
    records = AttendanceRecord.objects.select_related('member').order_by('-date', '-check_in')

    # Filters
    q          = request.GET.get('q', '')
    date_from  = request.GET.get('from', '')
    date_to    = request.GET.get('to', '')
    status_f   = request.GET.get('status', '')
    method_f   = request.GET.get('method', '')

    if q:
        records = records.filter(
            Q(member__first_name__icontains=q) |
            Q(member__last_name__icontains=q)  |
            Q(member__member_id__icontains=q)
        )
    if date_from:
        records = records.filter(date__gte=date_from)
    if date_to:
        records = records.filter(date__lte=date_to)
    if status_f:
        records = records.filter(status=status_f)
    if method_f:
        records = records.filter(check_in_method=method_f)

    return render(request, 'attendance/attendance_history.html', {
        'records':   records[:200],
        'total':     records.count(),
        'q':         q,
        'date_from': date_from,
        'date_to':   date_to,
        'status_f':  status_f,
        'method_f':  method_f,
        'statuses':  AttendanceRecord.Status.choices,
        'methods':   AttendanceRecord.CheckInMethod.choices,
    })


# ── 9. Member Attendance ───────────────────────────────────
@login_required
def member_attendance(request, pk):
    member  = get_object_or_404(Member, pk=pk)
    records = AttendanceRecord.objects.filter(
        member=member
    ).order_by('-date', '-check_in')

    today = timezone.now().date()
    month_ago = today - timedelta(days=30)

    stats = {
        'total_visits':    records.count(),
        'this_month':      records.filter(date__gte=month_ago).count(),
        'on_time':         records.filter(status='present').count(),
        'late':            records.filter(status='late').count(),
        'avg_duration':    records.filter(
                               check_in__isnull=False, check_out__isnull=False
                           ).aggregate(
                               avg=Avg(F('check_out') - F('check_in'))
                           )['avg'],
        'last_visit':      records.first(),
        'streak':          _calc_streak(member),
    }

    # Monthly trend — last 6 months
    monthly = []
    for i in range(5, -1, -1):
        d = today.replace(day=1) - timedelta(days=i * 30)
        c = records.filter(date__year=d.year, date__month=d.month).count()
        monthly.append({'label': d.strftime('%b'), 'count': c})

    return render(request, 'attendance/member_attendance.html', {
        'member':  member,
        'records': records[:50],
        'stats':   stats,
        'monthly': monthly,
        'today':   today,
    })


def _calc_streak(member):
    """Calculate current consecutive days streak."""
    today   = timezone.now().date()
    streak  = 0
    current = today
    while True:
        exists = AttendanceRecord.objects.filter(
            member=member, date=current
        ).exists()
        if exists:
            streak  += 1
            current -= timedelta(days=1)
        else:
            break
        if streak > 365:
            break
    return streak


# ── 10. Attendance Dashboard ───────────────────────────────
@login_required
def attendance_dashboard(request):
    today     = timezone.now().date()
    week_ago  = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Today's live stats
    today_records = AttendanceRecord.objects.filter(date=today)
    inside_now    = today_records.filter(check_out__isnull=True)

    stats = {
        'today_total':   today_records.count(),
        'inside_now':    inside_now.count(),
        'checked_out':   today_records.filter(check_out__isnull=False).count(),
        'late_today':    today_records.filter(status='late').count(),
        'this_week':     AttendanceRecord.objects.filter(date__gte=week_ago).count(),
        'this_month':    AttendanceRecord.objects.filter(date__gte=month_ago).count(),
        'avg_per_day':   round(
                             AttendanceRecord.objects.filter(date__gte=month_ago).count() / 30, 1
                         ),
        'peak_hour':     _get_peak_hour(),
    }

    # Weekly trend
    weekly = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        c = AttendanceRecord.objects.filter(date=d).count()
        weekly.append({'label': d.strftime('%a'), 'count': c, 'date': str(d)})

    # Hourly today
    hourly = (
        today_records.filter(check_in__isnull=False)
        .annotate(hour=TruncHour('check_in'))
        .values('hour')
        .annotate(count=Count('id'))
        .order_by('hour')
    )
    hourly_data = [
        {'hour': row['hour'].strftime('%H:00') if row['hour'] else '?',
         'count': row['count']}
        for row in hourly
    ]

    # Members currently inside
    inside_members = inside_now.select_related('member').order_by('-check_in')[:10]

    # Recent activity
    recent = AttendanceRecord.objects.select_related('member').order_by('-check_in')[:8]

    return render(request, 'attendance/dashboard.html', {
        'stats':          stats,
        'weekly':         weekly,
        'hourly':         hourly_data,
        'inside_members': inside_members,
        'recent':         recent,
        'today':          today,
        'now':            timezone.now(),
    })


def _get_peak_hour():
    try:
        result = (
            AttendanceRecord.objects
            .filter(check_in__isnull=False)
            .annotate(hour=TruncHour('check_in'))
            .values('hour')
            .annotate(count=Count('id'))
            .order_by('-count')
            .first()
        )
        if result and result['hour']:
            return result['hour'].strftime('%H:00')
    except Exception:
        pass
    return '—'


# ── 11. Attendance Reports ─────────────────────────────────
@login_required
def attendance_reports(request):
    today     = timezone.now().date()
    date_from = request.GET.get('from', str(today - timedelta(days=30)))
    date_to   = request.GET.get('to',   str(today))

    records = AttendanceRecord.objects.filter(
        date__gte=date_from, date__lte=date_to
    ).select_related('member')

    # Top members
    top_members = (
        records.values('member__first_name', 'member__last_name',
                       'member__member_id', 'member__pk')
        .annotate(visits=Count('id'))
        .order_by('-visits')[:10]
    )

    # Daily summary
    daily_summary = (
        records.values('date')
        .annotate(
            total=Count('id'),
            late=Count('id', filter=Q(status='late')),
        )
        .order_by('-date')[:30]
    )

    # Method breakdown
    method_stats = (
        records.values('check_in_method')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    stats = {
        'total':       records.count(),
        'unique_members': records.values('member').distinct().count(),
        'on_time':     records.filter(status='present').count(),
        'late':        records.filter(status='late').count(),
        'avg_per_day': round(records.count() / max((date.fromisoformat(date_to) - date.fromisoformat(date_from)).days, 1), 1),
    }

    return render(request, 'attendance/reports.html', {
        'stats':         stats,
        'top_members':   top_members,
        'daily_summary': daily_summary,
        'method_stats':  method_stats,
        'date_from':     date_from,
        'date_to':       date_to,
        'today':         today,
    })


# ── 12. Late Members ───────────────────────────────────────
@login_required
def late_members(request):
    today   = timezone.now().date()
    date_f  = request.GET.get('date', str(today))

    records = AttendanceRecord.objects.filter(
        date=date_f, status='late'
    ).select_related('member').order_by('-check_in')

    return render(request, 'attendance/late_members.html', {
        'records': records,
        'date_f':  date_f,
        'count':   records.count(),
        'today':   today,
    })


# ── 13. Absent Members ─────────────────────────────────────
@login_required
def absent_members(request):
    today   = timezone.now().date()
    date_f  = request.GET.get('date', str(today))

    # Active members who have no record on date_f
    attended_pks = AttendanceRecord.objects.filter(
        date=date_f
    ).values_list('member_id', flat=True)

    absent = Member.objects.filter(
        status='active'
    ).exclude(pk__in=attended_pks).order_by('first_name')

    # Streak info: members absent 3+ consecutive days
    chronic = []
    for m in absent:
        streak = 0
        d = today
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
        'absent':  absent,
        'count':   absent.count(),
        'chronic': chronic,
        'date_f':  date_f,
        'today':   today,
    })


# ── 14. Attendance Statistics ──────────────────────────────
@login_required
def attendance_statistics(request):
    today     = timezone.now().date()
    month_ago = today - timedelta(days=30)
    year_ago  = today - timedelta(days=365)

    # Monthly trend — last 12 months
    monthly = []
    for i in range(11, -1, -1):
        d = today.replace(day=1) - timedelta(days=i * 30)
        c = AttendanceRecord.objects.filter(
            date__year=d.year, date__month=d.month
        ).count()
        monthly.append({'label': d.strftime('%b %y'), 'count': c})

    # Weekday breakdown
    from django.db.models.functions import ExtractWeekDay
    weekday_data = (
        AttendanceRecord.objects.filter(date__gte=month_ago)
        .annotate(wd=ExtractWeekDay('date'))
        .values('wd')
        .annotate(count=Count('id'))
        .order_by('wd')
    )
    day_names = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    weekday_map = {row['wd']: row['count'] for row in weekday_data}
    weekday_chart = [
        {'day': day_names[i], 'count': weekday_map.get(i + 1, 0)}
        for i in range(7)
    ]

    # Method distribution
    method_dist = (
        AttendanceRecord.objects.filter(date__gte=month_ago)
        .values('check_in_method')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # Overall stats
    total_all   = AttendanceRecord.objects.count()
    total_month = AttendanceRecord.objects.filter(date__gte=month_ago).count()

    stats = {
        'total_all_time':    total_all,
        'total_this_month':  total_month,
        'total_this_year':   AttendanceRecord.objects.filter(date__gte=year_ago).count(),
        'unique_members':    AttendanceRecord.objects.values('member').distinct().count(),
        'avg_per_day':       round(total_month / 30, 1),
        'late_rate_pct':     round(
                                 AttendanceRecord.objects.filter(
                                     date__gte=month_ago, status='late'
                                 ).count() / max(total_month, 1) * 100, 1
                             ),
        'peak_hour':         _get_peak_hour(),
        'qr_usage_pct':      round(
                                 AttendanceRecord.objects.filter(
                                     date__gte=month_ago, check_in_method='qr'
                                 ).count() / max(total_month, 1) * 100, 1
                             ),
    }

    return render(request, 'attendance/statistics.html', {
        'stats':          stats,
        'monthly':        monthly,
        'weekday_chart':  weekday_chart,
        'method_dist':    method_dist,
        'today':          today,
    })


# ── AJAX endpoints ─────────────────────────────────────────
@login_required
def ajax_checkin(request):
    """POST: member_id, method → JSON"""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required'})

    data      = json.loads(request.body)
    member_id = data.get('member_id', '').strip()
    method    = data.get('method', 'qr')

    member = (
        Member.objects.filter(member_id=member_id).first() or
        Member.objects.filter(pk=member_id if member_id.isdigit() else 0).first()
    )
    if not member:
        return JsonResponse({'ok': False, 'error': f'Member "{member_id}" not found.'})

    record, err = _checkin_member(member, method=method, user=request.user)
    if err:
        return JsonResponse({'ok': False, 'error': err})

    return JsonResponse({
        'ok':     True,
        'name':   member.get_full_name(),
        'id':     member.member_id,
        'status': record.status,
        'time':   record.check_in.strftime('%H:%M'),
        'avatar': member.profile_image.url if member.profile_image else None,
    })


@login_required
def ajax_checkout(request):
    """POST: record_id, method → JSON"""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required'})

    data      = json.loads(request.body)
    record_id = data.get('record_id')
    method    = data.get('method', 'qr')

    try:
        record = AttendanceRecord.objects.select_related('member').get(
            pk=record_id, check_out__isnull=True
        )
    except AttendanceRecord.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Record not found or already checked out.'})

    record.do_checkout(method=method, recorded_by=request.user)
    return JsonResponse({
        'ok':       True,
        'name':     record.member.get_full_name(),
        'duration': record.duration_display,
        'time':     record.check_out.strftime('%H:%M'),
    })


@login_required
def ajax_live_count(request):
    """GET — returns current inside count for real-time update."""
    today = timezone.now().date()
    count = AttendanceRecord.objects.filter(
        date=today, check_out__isnull=True
    ).count()
    return JsonResponse({'count': count, 'time': timezone.now().strftime('%H:%M:%S')})
