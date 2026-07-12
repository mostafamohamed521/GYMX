from datetime import date, timedelta
from calendar import monthcalendar, monthrange

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from apps.accounts.permissions import role_required, STAFF_ROLES
from django.contrib import messages
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone

from .models import (
    Coach, CoachSpecialization, CoachCertificate, CoachNote,
    CoachAvailability, CoachSchedule, CoachAttendance,
    CoachSalary, CoachCommission,
)
from apps.members.models import Member
from apps.accounts.models import User


def _coach_context(pk):
    return get_object_or_404(Coach, pk=pk)


# ── 1. Coach List ──────────────────────────────────────────
@role_required(*STAFF_ROLES)
def coach_list(request):
    coaches = Coach.objects.prefetch_related('specializations').order_by('first_name')
    q       = request.GET.get('q', '')
    status  = request.GET.get('status', '')
    spec    = request.GET.get('spec', '')

    if q:
        coaches = coaches.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q)
        )
    if status:
        coaches = coaches.filter(status=status)
    if spec:
        coaches = coaches.filter(specializations__pk=spec)

    stats = {
        'total':    Coach.objects.count(),
        'active':   Coach.objects.filter(status='active').count(),
        'on_leave': Coach.objects.filter(status='on_leave').count(),
    }
    specs = CoachSpecialization.objects.all()

    return render(request, 'coaches/coach_list.html', {
        'coaches': coaches, 'stats': stats, 'specs': specs,
        'q': q, 'status_f': status, 'spec_f': spec,
        'statuses': Coach.Status.choices,
    })


# ── 2. Add Coach ───────────────────────────────────────────
@role_required(*STAFF_ROLES)
def coach_add(request):
    if request.method == 'POST':
        try:
            coach = Coach.objects.create(
                first_name      = request.POST.get('first_name'),
                last_name       = request.POST.get('last_name'),
                email           = request.POST.get('email'),
                phone           = request.POST.get('phone'),
                phone_secondary = request.POST.get('phone_secondary', ''),
                gender          = request.POST.get('gender', 'male'),
                birth_date      = request.POST.get('birth_date') or None,
                nationality     = request.POST.get('nationality', ''),
                national_id     = request.POST.get('national_id', ''),
                address         = request.POST.get('address', ''),
                status          = request.POST.get('status', 'active'),
                employment_type = request.POST.get('employment_type', 'full_time'),
                hire_date       = request.POST.get('hire_date') or timezone.now().date(),
                experience_years= int(request.POST.get('experience_years', 0)),
                bio             = request.POST.get('bio', ''),
                base_salary     = float(request.POST.get('base_salary', 0)),
                commission_rate = float(request.POST.get('commission_rate', 0)),
                session_rate    = float(request.POST.get('session_rate', 0)),
                max_members     = int(request.POST.get('max_members', 20)),
                instagram       = request.POST.get('instagram', ''),
                youtube         = request.POST.get('youtube', ''),
            )
            if 'profile_image' in request.FILES:
                coach.profile_image = request.FILES['profile_image']
                coach.save(update_fields=['profile_image'])

            spec_ids = request.POST.getlist('specializations')
            if spec_ids:
                coach.specializations.set(spec_ids)

            messages.success(request, f'Coach {coach.get_full_name()} added successfully!')
            return redirect('coaches:detail', pk=coach.pk)
        except Exception as e:
            messages.error(request, f'Error: {e}')

    specs = CoachSpecialization.objects.all()
    return render(request, 'coaches/coach_form.html', {
        'specs': specs, 'action': 'Add', 'page_title': 'Add Coach',
        'statuses': Coach.Status.choices,
        'employment_types': Coach.EmploymentType.choices,
        'today': timezone.now().date(),
    })


# ── 3. Coach Detail ────────────────────────────────────────
@role_required(*STAFF_ROLES)
def coach_detail(request, pk):
    coach   = _coach_context(pk)
    today   = timezone.now().date()
    month_ago = today - timedelta(days=30)

    assigned = Member.objects.filter(assigned_coach=coach.user) if coach.user else Member.objects.none()

    stats = {
        'assigned_members': assigned.count(),
        'attendance_month': CoachAttendance.objects.filter(coach=coach, date__gte=month_ago, status='present').count(),
        'sessions_month':   CoachSchedule.objects.filter(coach=coach, date__gte=month_ago, is_completed=True).count(),
        'commissions_total': CoachCommission.objects.filter(coach=coach).aggregate(t=Sum('amount'))['t'] or 0,
        'last_salary':      CoachSalary.objects.filter(coach=coach).first(),
        'rating':           coach.rating,
    }

    recent_schedule = CoachSchedule.objects.filter(coach=coach, date__gte=today).order_by('date','start_time')[:5]
    certificates    = coach.certificates.all()[:3]
    notes           = coach.notes.all()[:3]

    pages = [
        ('Schedule',      'fa-calendar-days',   'coaches:schedule'),
        ('Calendar',      'fa-calendar',        'coaches:calendar'),
        ('Members',       'fa-users',           'coaches:members'),
        ('Classes',       'fa-chalkboard',      'coaches:classes'),
        ('Attendance',    'fa-calendar-check',  'coaches:attendance'),
        ('Salary',        'fa-dollar-sign',     'coaches:salary'),
        ('Commissions',   'fa-coins',           'coaches:commissions'),
        ('Performance',   'fa-chart-line',      'coaches:performance'),
        ('Certificates',  'fa-certificate',     'coaches:certificates'),
        ('Notes',         'fa-note-sticky',     'coaches:notes'),
        ('Availability',  'fa-clock',           'coaches:availability'),
    ]
    return render(request, 'coaches/coach_detail.html', {
        'coach': coach, 'stats': stats,
        'assigned': assigned[:5],
        'recent_schedule': recent_schedule,
        'certificates': certificates,
        'notes': notes,
        'today': today,
        'pages': pages,
    })


# ── 4. Edit Coach ──────────────────────────────────────────
@role_required(*STAFF_ROLES)
def coach_edit(request, pk):
    coach = _coach_context(pk)
    if request.method == 'POST':
        try:
            coach.first_name       = request.POST.get('first_name', coach.first_name)
            coach.last_name        = request.POST.get('last_name', coach.last_name)
            coach.email            = request.POST.get('email', coach.email)
            coach.phone            = request.POST.get('phone', coach.phone)
            coach.phone_secondary  = request.POST.get('phone_secondary', '')
            coach.gender           = request.POST.get('gender', coach.gender)
            coach.birth_date       = request.POST.get('birth_date') or None
            coach.nationality      = request.POST.get('nationality', '')
            coach.national_id      = request.POST.get('national_id', '')
            coach.address          = request.POST.get('address', '')
            coach.status           = request.POST.get('status', coach.status)
            coach.employment_type  = request.POST.get('employment_type', coach.employment_type)
            coach.hire_date        = request.POST.get('hire_date') or coach.hire_date
            coach.experience_years = int(request.POST.get('experience_years', 0))
            coach.bio              = request.POST.get('bio', '')
            coach.base_salary      = float(request.POST.get('base_salary', 0))
            coach.commission_rate  = float(request.POST.get('commission_rate', 0))
            coach.session_rate     = float(request.POST.get('session_rate', 0))
            coach.max_members      = int(request.POST.get('max_members', 20))
            coach.instagram        = request.POST.get('instagram', '')
            coach.youtube          = request.POST.get('youtube', '')

            if 'profile_image' in request.FILES:
                coach.profile_image = request.FILES['profile_image']

            coach.save()
            spec_ids = request.POST.getlist('specializations')
            coach.specializations.set(spec_ids)

            messages.success(request, 'Coach updated!')
            return redirect('coaches:detail', pk=pk)
        except Exception as e:
            messages.error(request, f'Error: {e}')

    specs = CoachSpecialization.objects.all()
    return render(request, 'coaches/coach_form.html', {
        'coach': coach, 'specs': specs,
        'action': 'Edit', 'page_title': f'Edit — {coach.get_full_name()}',
        'statuses': Coach.Status.choices,
        'employment_types': Coach.EmploymentType.choices,
    })


# ── 5. Coach Schedule ──────────────────────────────────────
@role_required(*STAFF_ROLES)
def coach_schedule(request, pk):
    coach = _coach_context(pk)
    today = timezone.now().date()

    if request.method == 'POST':
        try:
            member_pk = request.POST.get('member')
            CoachSchedule.objects.create(
                coach        = coach,
                session_type = request.POST.get('session_type', 'pt'),
                title        = request.POST.get('title'),
                date         = request.POST.get('date'),
                start_time   = request.POST.get('start_time'),
                end_time     = request.POST.get('end_time'),
                member       = Member.objects.filter(pk=member_pk).first() if member_pk else None,
                notes        = request.POST.get('notes', ''),
            )
            messages.success(request, 'Session added to schedule.')
            return redirect('coaches:schedule', pk=pk)
        except Exception as e:
            messages.error(request, f'Error: {e}')

    week_start  = today - timedelta(days=today.weekday())
    week_end    = week_start + timedelta(days=6)
    this_week   = CoachSchedule.objects.filter(coach=coach, date__gte=week_start, date__lte=week_end).order_by('date','start_time')
    upcoming    = CoachSchedule.objects.filter(coach=coach, date__gte=today).order_by('date','start_time')[:20]
    members     = Member.objects.filter(assigned_coach=coach.user) if coach.user else Member.objects.none()

    return render(request, 'coaches/coach_schedule.html', {
        'coach': coach, 'this_week': this_week, 'upcoming': upcoming,
        'members': members, 'today': today,
        'week_start': week_start, 'week_end': week_end,
        'session_types': CoachSchedule.SessionType.choices,
    })


# ── 6. Coach Calendar ─────────────────────────────────────
@role_required(*STAFF_ROLES)
def coach_calendar(request, pk):
    coach = _coach_context(pk)
    today = timezone.now().date()
    year  = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    _, days_in_month = monthrange(year, month)
    start = date(year, month, 1)
    end   = date(year, month, days_in_month)

    sessions = CoachSchedule.objects.filter(coach=coach, date__gte=start, date__lte=end)
    sched_map = {}
    for s in sessions:
        sched_map.setdefault(s.date.day, []).append(s)

    if month == 1:
        py, pm = year-1, 12
    else:
        py, pm = year, month-1
    if month == 12:
        ny, nm = year+1, 1
    else:
        ny, nm = year, month+1

    return render(request, 'coaches/coach_calendar.html', {
        'coach': coach, 'year': year, 'month': month,
        'month_name': start.strftime('%B'),
        'cal_weeks': monthcalendar(year, month),
        'sched_map': sched_map,
        'today': today,
        'prev_year': py, 'prev_month': pm,
        'next_year': ny, 'next_month': nm,
    })


# ── 7. Assigned Members ────────────────────────────────────
@role_required(*STAFF_ROLES)
def assigned_members(request, pk):
    coach   = _coach_context(pk)
    members = Member.objects.filter(assigned_coach=coach.user).select_related('assigned_coach') if coach.user else Member.objects.none()
    all_members = Member.objects.filter(status='active').order_by('first_name')

    return render(request, 'coaches/assigned_members.html', {
        'coach': coach, 'members': members, 'count': members.count(),
        'all_members': all_members,
    })


# ── 8. Assigned Classes ────────────────────────────────────
@role_required(*STAFF_ROLES)
def assigned_classes(request, pk):
    coach   = _coach_context(pk)
    today   = timezone.now().date()
    classes = CoachSchedule.objects.filter(
        coach=coach, session_type='class'
    ).order_by('-date')

    upcoming = classes.filter(date__gte=today)
    past     = classes.filter(date__lt=today)

    return render(request, 'coaches/assigned_classes.html', {
        'coach': coach, 'upcoming': upcoming, 'past': past,
        'today': today,
    })


# ── 9. Coach Attendance ────────────────────────────────────
@role_required(*STAFF_ROLES)
def coach_attendance(request, pk):
    coach = _coach_context(pk)
    today = timezone.now().date()

    if request.method == 'POST':
        d      = request.POST.get('date', str(today))
        status = request.POST.get('status', 'present')
        cin    = request.POST.get('check_in') or None
        cout   = request.POST.get('check_out') or None
        att, _ = CoachAttendance.objects.update_or_create(
            coach=coach, date=d,
            defaults={'status': status, 'check_in': cin, 'check_out': cout,
                      'notes': request.POST.get('notes',''), 'recorded_by': request.user}
        )
        messages.success(request, f'Attendance for {d} recorded.')
        return redirect('coaches:attendance', pk=pk)

    month_ago  = today - timedelta(days=30)
    records    = CoachAttendance.objects.filter(coach=coach).order_by('-date')[:60]
    stats = {
        'present':  records.filter(status='present').count(),
        'absent':   records.filter(status='absent').count(),
        'late':     records.filter(status='late').count(),
        'leave':    records.filter(status='leave').count(),
    }

    return render(request, 'coaches/coach_attendance.html', {
        'coach': coach, 'records': records, 'stats': stats,
        'today': today, 'statuses': CoachAttendance.Status.choices,
    })


# ── 10. Coach Salary ───────────────────────────────────────
@role_required(*STAFF_ROLES)
def coach_salary(request, pk):
    coach = _coach_context(pk)

    if request.method == 'POST':
        month_str = request.POST.get('month')
        month_dt  = date.fromisoformat(month_str + '-01')
        comms = CoachCommission.objects.filter(
            coach=coach,
            date__year=month_dt.year, date__month=month_dt.month,
            is_paid=False
        ).aggregate(t=Sum('amount'))['t'] or 0

        salary, created = CoachSalary.objects.update_or_create(
            coach=coach, month=month_dt,
            defaults={
                'base_salary':  float(request.POST.get('base_salary', coach.base_salary)),
                'bonus':        float(request.POST.get('bonus', 0)),
                'deductions':   float(request.POST.get('deductions', 0)),
                'commissions':  float(comms),
                'status':       request.POST.get('status', 'pending'),
                'paid_date':    request.POST.get('paid_date') or None,
                'notes':        request.POST.get('notes', ''),
                'created_by':   request.user,
            }
        )
        messages.success(request, f'Salary {"created" if created else "updated"} for {month_dt.strftime("%B %Y")}.')
        return redirect('coaches:salary', pk=pk)

    salaries = CoachSalary.objects.filter(coach=coach).order_by('-month')
    total_paid = salaries.filter(status='paid').aggregate(t=Sum('net_salary'))['t'] or 0
    today = timezone.now().date()

    return render(request, 'coaches/coach_salary.html', {
        'coach': coach, 'salaries': salaries,
        'total_paid': total_paid, 'today': today,
        'statuses': CoachSalary.Status.choices,
        'current_month': today.strftime('%Y-%m'),
    })


# ── 11. Coach Commissions ──────────────────────────────────
@role_required(*STAFF_ROLES)
def coach_commissions(request, pk):
    coach = _coach_context(pk)

    if request.method == 'POST':
        member_pk = request.POST.get('member')
        CoachCommission.objects.create(
            coach       = coach,
            member      = get_object_or_404(Member, pk=member_pk),
            description = request.POST.get('description'),
            amount      = float(request.POST.get('amount', 0)),
            date        = request.POST.get('date') or timezone.now().date(),
            notes       = request.POST.get('notes', ''),
        )
        messages.success(request, 'Commission recorded.')
        return redirect('coaches:commissions', pk=pk)

    commissions = CoachCommission.objects.filter(coach=coach).select_related('member').order_by('-date')
    stats = {
        'total':   commissions.aggregate(t=Sum('amount'))['t'] or 0,
        'paid':    commissions.filter(is_paid=True).aggregate(t=Sum('amount'))['t'] or 0,
        'pending': commissions.filter(is_paid=False).aggregate(t=Sum('amount'))['t'] or 0,
        'count':   commissions.count(),
    }
    members = Member.objects.filter(assigned_coach=coach.user) if coach.user else Member.objects.none()

    return render(request, 'coaches/coach_commissions.html', {
        'coach': coach, 'commissions': commissions,
        'stats': stats, 'members': members,
        'today': timezone.now().date(),
    })


# ── 12. Coach Performance ──────────────────────────────────
@role_required(*STAFF_ROLES)
def coach_performance(request, pk):
    coach     = _coach_context(pk)
    today     = timezone.now().date()
    month_ago = today - timedelta(days=30)

    sessions_total     = CoachSchedule.objects.filter(coach=coach).count()
    sessions_completed = CoachSchedule.objects.filter(coach=coach, is_completed=True).count()
    sessions_month     = CoachSchedule.objects.filter(coach=coach, date__gte=month_ago).count()

    attendance_total   = CoachAttendance.objects.filter(coach=coach).count()
    attendance_present = CoachAttendance.objects.filter(coach=coach, status='present').count()
    attendance_rate    = round(attendance_present / max(attendance_total, 1) * 100, 1)

    members_assigned   = Member.objects.filter(assigned_coach=coach.user).count() if coach.user else 0
    commissions_total  = CoachCommission.objects.filter(coach=coach).aggregate(t=Sum('amount'))['t'] or 0

    monthly_sessions = []
    for i in range(5, -1, -1):
        d = today.replace(day=1) - timedelta(days=i*30)
        c = CoachSchedule.objects.filter(coach=coach, date__year=d.year, date__month=d.month).count()
        monthly_sessions.append({'label': d.strftime('%b'), 'count': c})

    return render(request, 'coaches/coach_performance.html', {
        'coach': coach,
        'sessions_total': sessions_total,
        'sessions_completed': sessions_completed,
        'sessions_month': sessions_month,
        'completion_rate': round(sessions_completed / max(sessions_total, 1) * 100, 1),
        'attendance_rate': attendance_rate,
        'members_assigned': members_assigned,
        'commissions_total': commissions_total,
        'monthly_sessions': monthly_sessions,
        'today': today,
    })


# ── 13. Coach Certificates ────────────────────────────────
@role_required(*STAFF_ROLES)
def coach_certificates(request, pk):
    coach = _coach_context(pk)

    if request.method == 'POST':
        cert = CoachCertificate(
            coach      = coach,
            title      = request.POST.get('title'),
            issued_by  = request.POST.get('issued_by'),
            issue_date = request.POST.get('issue_date'),
            expiry_date= request.POST.get('expiry_date') or None,
        )
        if 'document' in request.FILES:
            cert.document = request.FILES['document']
        cert.save()
        messages.success(request, 'Certificate added.')
        return redirect('coaches:certificates', pk=pk)

    certs = coach.certificates.all()
    return render(request, 'coaches/coach_certificates.html', {
        'coach': coach, 'certs': certs, 'today': timezone.now().date(),
    })


# ── 14. Coach Notes ────────────────────────────────────────
@role_required(*STAFF_ROLES)
def coach_notes(request, pk):
    coach = _coach_context(pk)

    if request.method == 'POST':
        if request.POST.get('action') == 'delete':
            note = get_object_or_404(CoachNote, pk=request.POST.get('note_id'), coach=coach)
            note.delete()
            messages.success(request, 'Note deleted.')
        else:
            CoachNote.objects.create(
                coach      = coach,
                title      = request.POST.get('title'),
                body       = request.POST.get('body'),
                priority   = request.POST.get('priority', 'normal'),
                is_pinned  = bool(request.POST.get('is_pinned')),
                created_by = request.user,
            )
            messages.success(request, 'Note added.')
        return redirect('coaches:notes', pk=pk)

    notes = coach.notes.all()
    return render(request, 'coaches/coach_notes.html', {
        'coach': coach, 'notes': notes,
        'priorities': CoachNote.Priority.choices,
    })


# ── 15. Coach Availability ────────────────────────────────
@role_required(*STAFF_ROLES)
def coach_availability(request, pk):
    coach = _coach_context(pk)

    if request.method == 'POST':
        CoachAvailability.objects.filter(coach=coach).delete()
        days = request.POST.getlist('day')
        for d in days:
            CoachAvailability.objects.create(
                coach        = coach,
                day_of_week  = int(d),
                start_time   = request.POST.get(f'start_{d}', '06:00'),
                end_time     = request.POST.get(f'end_{d}', '22:00'),
                is_available = True,
            )
        messages.success(request, 'Availability updated.')
        return redirect('coaches:availability', pk=pk)

    availability = {a.day_of_week: a for a in coach.availability.all()}
    days = [(i, name) for i, name in CoachAvailability.DAYS]

    return render(request, 'coaches/coach_availability.html', {
        'coach': coach, 'availability': availability, 'days': days,
    })
