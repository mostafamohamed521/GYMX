from datetime import date, timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg

from apps.members.models import Member
from apps.memberships.models import MemberSubscription
from apps.attendance.models import AttendanceRecord
from apps.payments.models import Payment, Invoice
from apps.coaches.models import Coach
from apps.workouts.models import WorkoutPlan, WorkoutSession, PTSession
from apps.nutrition.models import NutritionPlan
from apps.classes.models import ClassSession, ClassBooking
from apps.hr.models import Employee, LeaveRequest
from apps.inventory.models import Product
from apps.pos.models import Sale


@login_required
def index_view(request):
    user  = request.user
    today = date.today()
    month_ago = today - timedelta(days=30)

    # ── Super Admin / Gym Manager: full business overview ──
    if user.is_superuser or user.role in ('super_admin', 'gym_manager'):
        stats = {
            'total_members':    Member.objects.count(),
            'active_members':   Member.objects.filter(status='active').count(),
            'new_this_month':   Member.objects.filter(created_at__gte=month_ago).count(),
            'total_coaches':    Coach.objects.filter(status='active').count(),
            'total_employees':  Employee.objects.filter(status='active').count(),
            'monthly_revenue':  Payment.objects.filter(status='completed', payment_date__gte=month_ago).aggregate(t=Sum('net_amount'))['t'] or 0,
            'pos_revenue':      Sale.objects.filter(status='completed', created_at__date__gte=month_ago).aggregate(t=Sum('total'))['t'] or 0,
            'attendance_today': AttendanceRecord.objects.filter(date=today).count(),
            'active_subs':      MemberSubscription.objects.filter(status='active').count(),
            'pending_payments': Payment.objects.filter(status='pending').count(),
            'overdue_invoices': Invoice.objects.filter(status='overdue').count(),
            'low_stock':        sum(1 for p in Product.objects.filter(is_active=True) if p.is_low_stock),
            'pending_leave':    LeaveRequest.objects.filter(status='pending').count(),
        }
        recent_members  = Member.objects.order_by('-created_at')[:5]
        recent_payments = Payment.objects.filter(status='completed').select_related('member').order_by('-created_at')[:5]
        top_coaches     = Coach.objects.filter(status='active').order_by('-rating')[:4]

        return render(request, 'dashboard/index_admin.html', {
            'stats': stats, 'recent_members': recent_members,
            'recent_payments': recent_payments, 'top_coaches': top_coaches,
            'page_title': 'Dashboard',
        })

    # ── Receptionist: front-desk operations ─────────────────
    if user.role == 'receptionist':
        stats = {
            'checkins_today':   AttendanceRecord.objects.filter(date=today).count(),
            'new_this_week':    Member.objects.filter(created_at__gte=today - timedelta(days=7)).count(),
            'pending_payments': Payment.objects.filter(status='pending').count(),
            'expiring_soon':    MemberSubscription.objects.filter(status='active', end_date__lte=today + timedelta(days=7), end_date__gte=today).count(),
        }
        recent_checkins = AttendanceRecord.objects.filter(date=today).select_related('member').order_by('-check_in')[:8]
        pending_pay     = Payment.objects.filter(status='pending').select_related('member')[:5]
        upcoming_classes = ClassSession.objects.filter(date__gte=today, status='scheduled').select_related('gym_class').order_by('date','start_time')[:5]

        return render(request, 'dashboard/index_receptionist.html', {
            'stats': stats, 'recent_checkins': recent_checkins,
            'pending_pay': pending_pay, 'upcoming_classes': upcoming_classes,
            'page_title': 'Dashboard',
        })

    # ── Coach: their own members, schedule & sessions ───────
    if user.role == 'coach':
        coach = Coach.objects.filter(user=user).first()
        assigned_members = Member.objects.filter(assigned_coach=user) if coach else Member.objects.none()

        stats = {
            'my_members':      assigned_members.count(),
            'sessions_today':  PTSession.objects.filter(coach=coach, date=today).count() if coach else 0,
            'sessions_week':   PTSession.objects.filter(coach=coach, date__gte=today, date__lte=today+timedelta(days=7)).count() if coach else 0,
            'classes_today':   ClassSession.objects.filter(coach=coach, date=today).count() if coach else 0,
        }
        today_sessions = PTSession.objects.filter(coach=coach, date=today).select_related('member').order_by('start_time') if coach else PTSession.objects.none()
        my_classes     = ClassSession.objects.filter(coach=coach, date__gte=today).select_related('gym_class').order_by('date','start_time')[:5] if coach else ClassSession.objects.none()

        return render(request, 'dashboard/index_coach.html', {
            'coach': coach, 'stats': stats, 'assigned_members': assigned_members[:8],
            'today_sessions': today_sessions, 'my_classes': my_classes,
            'page_title': 'Dashboard',
        })

    # ── Member: their own portal snapshot ───────────────────
    member = Member.objects.filter(user=user).first()
    active_sub = MemberSubscription.objects.filter(member=member, status='active').select_related('plan').first() if member else None
    stats = {
        'membership_status': active_sub.get_status_display() if active_sub else 'No Active Plan',
        'days_left':         (active_sub.end_date - today).days if active_sub and active_sub.end_date else None,
        'attendance_month':  AttendanceRecord.objects.filter(member=member, date__gte=month_ago).count() if member else 0,
        'active_workout':    WorkoutPlan.objects.filter(member=member, status='active').first() if member else None,
        'active_nutrition':  NutritionPlan.objects.filter(member=member, status='active').first() if member else None,
        'upcoming_classes':  ClassBooking.objects.filter(member=member, status='confirmed', session__date__gte=today).count() if member else 0,
    }
    recent_payments = Payment.objects.filter(member=member).order_by('-payment_date')[:5] if member else []
    upcoming_sessions = WorkoutSession.objects.filter(plan__member=member, status='scheduled').order_by('scheduled_date')[:5] if member else []

    return render(request, 'dashboard/index_member.html', {
        'member': member, 'active_sub': active_sub, 'stats': stats,
        'recent_payments': recent_payments, 'upcoming_sessions': upcoming_sessions,
        'page_title': 'Dashboard',
    })
