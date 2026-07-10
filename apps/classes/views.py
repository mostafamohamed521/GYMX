from datetime import date, timedelta
from calendar import monthcalendar, monthrange
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone

from .models import GymClass, ClassCategory, ClassSchedule, ClassSession, ClassBooking, ClassAttendance
from apps.members.models import Member
from apps.coaches.models import Coach


@login_required
def classes_list(request):
    classes  = GymClass.objects.select_related('coach','category').order_by('name')
    q        = request.GET.get('q','')
    status_f = request.GET.get('status','')
    cat_f    = request.GET.get('category','')
    if q:        classes = classes.filter(Q(name__icontains=q)|Q(description__icontains=q))
    if status_f: classes = classes.filter(status=status_f)
    if cat_f:    classes = classes.filter(category__pk=cat_f)

    stats = {
        'total':    GymClass.objects.count(),
        'active':   GymClass.objects.filter(status='active').count(),
        'today':    ClassSession.objects.filter(date=date.today()).count(),
        'bookings': ClassBooking.objects.filter(status='confirmed').count(),
    }
    cats = ClassCategory.objects.all()
    return render(request, 'classes/classes_list.html', {
        'classes': classes, 'stats': stats, 'cats': cats,
        'q': q, 'status_f': status_f, 'cat_f': cat_f,
        'statuses': GymClass.Status.choices,
    })


@login_required
def class_add(request):
    if request.method == 'POST':
        try:
            cat_pk   = request.POST.get('category')
            coach_pk = request.POST.get('coach')
            cls = GymClass.objects.create(
                name           = request.POST.get('name'),
                category       = ClassCategory.objects.filter(pk=cat_pk).first() if cat_pk else None,
                coach          = Coach.objects.filter(pk=coach_pk).first() if coach_pk else None,
                description    = request.POST.get('description',''),
                difficulty     = request.POST.get('difficulty','all'),
                duration_min   = int(request.POST.get('duration_min',60)),
                max_capacity   = int(request.POST.get('max_capacity',20)),
                room           = request.POST.get('room',''),
                equipment_needed = request.POST.get('equipment_needed',''),
                calories_burn  = int(request.POST.get('calories_burn',300)),
                color          = request.POST.get('color','#3B82F6'),
                created_by     = request.user,
            )
            # Create schedule slots
            days    = request.POST.getlist('days')
            starts  = request.POST.getlist('start_times')
            ends    = request.POST.getlist('end_times')
            for d, st, et in zip(days, starts, ends):
                if d and st and et:
                    ClassSchedule.objects.create(gym_class=cls, day_of_week=int(d), start_time=st, end_time=et)
            messages.success(request, f'Class "{cls.name}" created!')
            return redirect('classes:detail', pk=cls.pk)
        except Exception as e:
            messages.error(request, f'Error: {e}')

    cats    = ClassCategory.objects.all()
    coaches = Coach.objects.filter(status='active')
    days    = ClassSchedule.DAYS
    return render(request, 'classes/class_form.html', {
        'cats': cats, 'coaches': coaches, 'days': days,
        'difficulties': GymClass.Difficulty.choices,
        'action': 'Add', 'page_title': 'Add Class',
    })


@login_required
def class_detail(request, pk):
    cls      = get_object_or_404(GymClass.objects.select_related('coach','category'), pk=pk)
    today    = date.today()
    schedules= cls.schedules.all()
    upcoming = ClassSession.objects.filter(gym_class=cls, date__gte=today).order_by('date','start_time')[:10]
    past     = ClassSession.objects.filter(gym_class=cls, date__lt=today).order_by('-date')[:5]

    stats = {
        'total_sessions':  ClassSession.objects.filter(gym_class=cls).count(),
        'total_bookings':  ClassBooking.objects.filter(session__gym_class=cls, status__in=['confirmed','attended']).count(),
        'avg_attendance':  ClassAttendance.objects.filter(session__gym_class=cls).values('session').annotate(c=Count('id')).aggregate(a=Avg('c'))['a'] or 0,
        'upcoming':        upcoming.count(),
    }

    if request.method == 'POST':
        # Quick-create a session
        try:
            ClassSession.objects.create(
                gym_class=cls, coach=cls.coach,
                date=request.POST.get('date'),
                start_time=request.POST.get('start_time','08:00'),
                end_time=request.POST.get('end_time','09:00'),
                notes=request.POST.get('notes',''),
            )
            messages.success(request, 'Session added.')
            return redirect('classes:detail', pk=pk)
        except Exception as e:
            messages.error(request, f'Error: {e}')

    return render(request, 'classes/class_detail.html', {
        'cls': cls, 'schedules': schedules, 'upcoming': upcoming,
        'past': past, 'stats': stats, 'today': today,
    })


@login_required
def class_edit(request, pk):
    cls = get_object_or_404(GymClass, pk=pk)
    if request.method == 'POST':
        try:
            cat_pk   = request.POST.get('category')
            coach_pk = request.POST.get('coach')
            cls.name           = request.POST.get('name', cls.name)
            cls.category       = ClassCategory.objects.filter(pk=cat_pk).first() if cat_pk else None
            cls.coach          = Coach.objects.filter(pk=coach_pk).first() if coach_pk else None
            cls.description    = request.POST.get('description','')
            cls.difficulty     = request.POST.get('difficulty', cls.difficulty)
            cls.duration_min   = int(request.POST.get('duration_min', cls.duration_min))
            cls.max_capacity   = int(request.POST.get('max_capacity', cls.max_capacity))
            cls.status         = request.POST.get('status', cls.status)
            cls.room           = request.POST.get('room','')
            cls.calories_burn  = int(request.POST.get('calories_burn', cls.calories_burn))
            cls.color          = request.POST.get('color', cls.color)
            cls.save()
            messages.success(request, 'Class updated!')
            return redirect('classes:detail', pk=pk)
        except Exception as e:
            messages.error(request, f'Error: {e}')

    cats    = ClassCategory.objects.all()
    coaches = Coach.objects.filter(status='active')
    days    = ClassSchedule.DAYS
    return render(request, 'classes/class_form.html', {
        'cls': cls, 'cats': cats, 'coaches': coaches, 'days': days,
        'difficulties': GymClass.Difficulty.choices,
        'statuses': GymClass.Status.choices,
        'action': 'Edit', 'page_title': f'Edit — {cls.name}',
    })


@login_required
def weekly_schedule(request):
    today      = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end   = week_start + timedelta(days=6)

    offset = int(request.GET.get('offset', 0))
    week_start += timedelta(weeks=offset)
    week_end   = week_start + timedelta(days=6)

    sessions = ClassSession.objects.filter(
        date__gte=week_start, date__lte=week_end,
        status__in=['scheduled','in_progress']
    ).select_related('gym_class','coach').order_by('date','start_time')

    week_days = [(week_start + timedelta(days=i)) for i in range(7)]
    day_map   = {d: [] for d in week_days}
    for s in sessions:
        if s.date in day_map:
            day_map[s.date].append(s)

    prev_offset = offset - 1
    next_offset = offset + 1

    return render(request, 'classes/weekly_schedule.html', {
        'day_map': day_map, 'week_days': week_days,
        'week_start': week_start, 'week_end': week_end,
        'today': today, 'offset': offset,
        'prev_offset': prev_offset, 'next_offset': next_offset,
    })


@login_required
def monthly_calendar(request):
    today = date.today()
    year  = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    _, days_in_month = monthrange(year, month)
    start = date(year, month, 1)
    end   = date(year, month, days_in_month)

    sessions = ClassSession.objects.filter(date__gte=start, date__lte=end).select_related('gym_class')
    smap = {}
    for s in sessions:
        smap.setdefault(s.date.day, []).append(s)

    py, pm = (year-1, 12) if month == 1 else (year, month-1)
    ny, nm = (year+1, 1) if month == 12 else (year, month+1)

    return render(request, 'classes/monthly_calendar.html', {
        'year': year, 'month': month, 'month_name': start.strftime('%B'),
        'cal_weeks': monthcalendar(year, month), 'smap': smap,
        'today': today, 'prev_year': py, 'prev_month': pm,
        'next_year': ny, 'next_month': nm,
    })


@login_required
def booking(request, pk):
    session = get_object_or_404(ClassSession.objects.select_related('gym_class','coach'), pk=pk)
    bookings = session.bookings.select_related('member').order_by('-booked_at')

    if request.method == 'POST':
        member_pk = request.POST.get('member')
        member = get_object_or_404(Member, pk=member_pk)
        if ClassBooking.objects.filter(session=session, member=member).exists():
            messages.warning(request, f'{member.get_full_name()} is already booked.')
        elif session.is_full:
            # Add to waitlist
            pos = session.bookings.filter(status='waitlist').count() + 1
            ClassBooking.objects.create(session=session, member=member, status='waitlist', waitlist_pos=pos)
            messages.info(request, f'{member.get_full_name()} added to waitlist (pos #{pos}).')
        else:
            ClassBooking.objects.create(session=session, member=member, status='confirmed')
            messages.success(request, f'{member.get_full_name()} booked successfully!')
        return redirect('classes:booking', pk=pk)

    members = Member.objects.filter(status='active').order_by('first_name')
    booked_ids = set(session.bookings.values_list('member_id', flat=True))

    return render(request, 'classes/booking.html', {
        'session': session, 'bookings': bookings,
        'members': members, 'booked_ids': booked_ids,
    })


@login_required
def cancel_booking(request, pk, member_pk):
    session = get_object_or_404(ClassSession, pk=pk)
    booking = get_object_or_404(ClassBooking, session=session, member__pk=member_pk)
    booking.status = 'cancelled'
    booking.save()
    # Promote from waitlist
    next_wait = session.bookings.filter(status='waitlist').order_by('waitlist_pos').first()
    if next_wait and not session.is_full:
        next_wait.status = 'confirmed'
        next_wait.waitlist_pos = None
        next_wait.save()
        messages.info(request, f'{next_wait.member.get_full_name()} promoted from waitlist.')
    messages.success(request, 'Booking cancelled.')
    return redirect('classes:booking', pk=pk)


@login_required
def waiting_list(request, pk):
    session  = get_object_or_404(ClassSession.objects.select_related('gym_class'), pk=pk)
    waitlist = session.bookings.filter(status='waitlist').select_related('member').order_by('waitlist_pos')

    return render(request, 'classes/waiting_list.html', {
        'session': session, 'waitlist': waitlist,
    })


@login_required
def class_attendance(request, pk):
    session  = get_object_or_404(ClassSession.objects.select_related('gym_class'), pk=pk)
    bookings = session.bookings.filter(status__in=['confirmed','attended','no_show']).select_related('member')

    if request.method == 'POST':
        attended_ids = request.POST.getlist('attended')
        for b in bookings:
            new_status = 'attended' if str(b.member.pk) in attended_ids else 'no_show'
            b.status = new_status
            b.save(update_fields=['status'])
            ClassAttendance.objects.update_or_create(
                session=session, member=b.member,
                defaults={'attended': new_status == 'attended'}
            )
        session.status = 'completed'
        session.save(update_fields=['status'])
        messages.success(request, f'Attendance saved — {len(attended_ids)} present.')
        return redirect('classes:detail', pk=session.gym_class.pk)

    return render(request, 'classes/class_attendance.html', {
        'session': session, 'bookings': bookings,
    })


@login_required
def capacity_management(request):
    today    = date.today()
    sessions = ClassSession.objects.filter(
        date__gte=today, status='scheduled'
    ).select_related('gym_class').order_by('date','start_time').annotate(
        confirmed_count=Count('bookings', filter=Q(bookings__status='confirmed'))
    )

    return render(request, 'classes/capacity_management.html', {
        'sessions': sessions, 'today': today,
    })


@login_required
def class_statistics(request):
    today     = date.today()
    month_ago = today - timedelta(days=30)

    stats = {
        'total_classes':   GymClass.objects.count(),
        'active_classes':  GymClass.objects.filter(status='active').count(),
        'total_sessions':  ClassSession.objects.count(),
        'total_bookings':  ClassBooking.objects.filter(status__in=['confirmed','attended']).count(),
        'attendance_rate': 0,
        'popular_class':   None,
    }

    attended = ClassBooking.objects.filter(status='attended').count()
    confirmed = ClassBooking.objects.filter(status__in=['confirmed','attended']).count()
    stats['attendance_rate'] = round(attended / max(confirmed, 1) * 100, 1)

    popular = (ClassBooking.objects.filter(status__in=['confirmed','attended'])
               .values('session__gym_class__name','session__gym_class__pk')
               .annotate(count=Count('id')).order_by('-count').first())
    stats['popular_class'] = popular

    monthly = []
    for i in range(5,-1,-1):
        d = today.replace(day=1) - timedelta(days=i*30)
        c = ClassSession.objects.filter(date__year=d.year, date__month=d.month, status='completed').count()
        b = ClassBooking.objects.filter(session__date__year=d.year, session__date__month=d.month, status__in=['confirmed','attended']).count()
        monthly.append({'label': d.strftime('%b'), 'sessions': c, 'bookings': b})

    top_classes = (ClassBooking.objects.filter(status__in=['confirmed','attended'])
                   .values('session__gym_class__name','session__gym_class__pk','session__gym_class__color')
                   .annotate(bookings=Count('id')).order_by('-bookings')[:8])

    return render(request, 'classes/class_statistics.html', {
        'stats': stats, 'monthly': monthly, 'top_classes': top_classes, 'today': today,
    })
