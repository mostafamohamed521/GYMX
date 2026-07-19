from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from functools import wraps

from apps.members.models import Member
from apps.memberships.models import MemberSubscription, MembershipPlan
from apps.attendance.models import AttendanceRecord
from apps.payments.models import Payment, Invoice
from apps.workouts.models import WorkoutPlan, WorkoutSession
from apps.nutrition.models import NutritionPlan, NutritionLog
from apps.classes.models import ClassBooking
from apps.coaches.models import Coach
from .models import SupportTicket, TicketReply, FreezeRequest, RenewalRequest


def member_required(view_func):
    """Ensures the logged-in user has a linked Member profile; injects `member` kwarg."""
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        member = Member.objects.filter(user=request.user).first()
        if not member:
            messages.error(request, "Your account isn't linked to a member profile. Please contact the front desk.")
            return redirect('dashboard:index')
        return view_func(request, member, *args, **kwargs)
    return _wrapped


# ── 1. Member Dashboard (portal-specific quick links page) ──
@member_required
def member_dashboard(request, member):
    active_sub = MemberSubscription.objects.filter(member=member, status='active').select_related('plan').first()
    today = date.today()
    stats = {
        'days_left': (active_sub.end_date - today).days if active_sub else None,
        'attendance_month': AttendanceRecord.objects.filter(member=member, date__gte=today-timedelta(days=30)).count(),
        'open_tickets': SupportTicket.objects.filter(member=member).exclude(status='closed').count(),
    }
    return render(request, 'portal/member_dashboard.html', {'member': member, 'active_sub': active_sub, 'stats': stats})


# ── 2. My Membership ──────────────────────────────────────────
@member_required
def my_membership(request, member):
    subscriptions = MemberSubscription.objects.filter(member=member).select_related('plan').order_by('-start_date')
    active_sub = subscriptions.filter(status='active').first()
    return render(request, 'portal/my_membership.html', {
        'member': member, 'subscriptions': subscriptions, 'active_sub': active_sub,
    })


# ── 3. Renew Membership ────────────────────────────────────────
@member_required
def renew_membership(request, member):
    active_sub = MemberSubscription.objects.filter(member=member, status='active').select_related('plan').first()
    if request.method == 'POST':
        plan_pk = request.POST.get('plan')
        RenewalRequest.objects.create(
            member=member, subscription=active_sub,
            requested_plan=MembershipPlan.objects.filter(pk=plan_pk).first() if plan_pk else (active_sub.plan if active_sub else None),
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, 'Renewal request submitted! Front desk will process it shortly.')
        return redirect('portal:membership')

    plans = MembershipPlan.objects.filter(is_active=True)
    past_requests = RenewalRequest.objects.filter(member=member).order_by('-created_at')[:5]
    return render(request, 'portal/renew_membership.html', {
        'member': member, 'active_sub': active_sub, 'plans': plans, 'past_requests': past_requests,
    })


# ── 4. Freeze Request ───────────────────────────────────────────
@member_required
def freeze_request(request, member):
    if request.method == 'POST':
        FreezeRequest.objects.create(
            member=member, start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'), reason=request.POST.get('reason', ''),
        )
        messages.success(request, 'Freeze request submitted for review.')
        return redirect('portal:freeze')

    requests_list = FreezeRequest.objects.filter(member=member).order_by('-created_at')
    return render(request, 'portal/freeze_request.html', {
        'member': member, 'requests_list': requests_list, 'today': date.today(),
    })


# ── 5. My Payments ───────────────────────────────────────────────
@member_required
def my_payments(request, member):
    payments = Payment.objects.filter(member=member).order_by('-payment_date')
    return render(request, 'portal/my_payments.html', {'member': member, 'payments': payments})


# ── 6. My Invoices ────────────────────────────────────────────────
@member_required
def my_invoices(request, member):
    invoices = Invoice.objects.filter(member=member).order_by('-issue_date')
    return render(request, 'portal/my_invoices.html', {'member': member, 'invoices': invoices})


# ── 7. My Attendance ──────────────────────────────────────────────
@member_required
def my_attendance(request, member):
    records = AttendanceRecord.objects.filter(member=member).order_by('-date')[:60]
    stats = {
        'total': AttendanceRecord.objects.filter(member=member).count(),
        'this_month': AttendanceRecord.objects.filter(member=member, date__gte=date.today().replace(day=1)).count(),
    }
    return render(request, 'portal/my_attendance.html', {'member': member, 'records': records, 'stats': stats})


# ── 8. My Workout ─────────────────────────────────────────────────
@member_required
def my_workout(request, member):
    plans = WorkoutPlan.objects.filter(member=member).order_by('-created_at')
    active_plan = plans.filter(status='active').first()
    sessions = WorkoutSession.objects.filter(plan=active_plan).order_by('scheduled_date') if active_plan else []
    return render(request, 'portal/my_workout.html', {
        'member': member, 'plans': plans, 'active_plan': active_plan, 'sessions': sessions,
    })


# ── 9. My Nutrition ───────────────────────────────────────────────
@member_required
def my_nutrition(request, member):
    plans = NutritionPlan.objects.filter(member=member).order_by('-created_at')
    active_plan = plans.filter(status='active').first()
    logs = NutritionLog.objects.filter(member=member).order_by('-date')[:14]
    return render(request, 'portal/my_nutrition.html', {
        'member': member, 'plans': plans, 'active_plan': active_plan, 'logs': logs,
    })


# ── 10. My Classes ────────────────────────────────────────────────
@member_required
def my_classes(request, member):
    bookings = ClassBooking.objects.filter(member=member).select_related('session__gym_class').order_by('-session__date')
    upcoming = bookings.filter(session__date__gte=date.today(), status='confirmed')
    return render(request, 'portal/my_classes.html', {
        'member': member, 'bookings': bookings, 'upcoming': upcoming,
    })


# ── 11. My Coach ──────────────────────────────────────────────────
@member_required
def my_coach(request, member):
    coach = None
    if member.assigned_coach:
        coach = Coach.objects.filter(user=member.assigned_coach).first()
    return render(request, 'portal/my_coach.html', {'member': member, 'coach': coach})


# ── 12. My QR Code ────────────────────────────────────────────────
@member_required
def my_qr_code(request, member):
    if not member.qr_code:
        member.generate_qr()
        member.save(update_fields=['qr_code'])
    return render(request, 'portal/my_qr_code.html', {'member': member})


# ── 13. Download Membership Card ──────────────────────────────────
@member_required
def membership_card(request, member):
    active_sub = MemberSubscription.objects.filter(member=member, status='active').select_related('plan').first()
    if not member.qr_code:
        member.generate_qr()
        member.save(update_fields=['qr_code'])
    return render(request, 'portal/membership_card.html', {'member': member, 'active_sub': active_sub})


# ── 14. Support Tickets ────────────────────────────────────────────
@member_required
def support_tickets(request, member):
    tickets = SupportTicket.objects.filter(member=member).order_by('-created_at')
    return render(request, 'portal/support_tickets.html', {'member': member, 'tickets': tickets})


@member_required
def support_ticket_new(request, member):
    if request.method == 'POST':
        ticket = SupportTicket.objects.create(
            member=member, subject=request.POST.get('subject'),
            description=request.POST.get('description'), category=request.POST.get('category', 'other'),
        )
        messages.success(request, 'Support ticket submitted!')
        return redirect('portal:support_detail', pk=ticket.pk)
    return render(request, 'portal/support_ticket_form.html', {
        'member': member, 'categories': SupportTicket.Category.choices,
    })


@member_required
def support_ticket_detail(request, member, pk):
    ticket = get_object_or_404(SupportTicket, pk=pk, member=member)
    if request.method == 'POST':
        TicketReply.objects.create(ticket=ticket, author=request.user, message=request.POST.get('message'))
        messages.success(request, 'Reply sent.')
        return redirect('portal:support_detail', pk=pk)
    replies = ticket.replies.select_related('author').order_by('created_at')
    return render(request, 'portal/support_ticket_detail.html', {'member': member, 'ticket': ticket, 'replies': replies})


# ── 15. My Profile ────────────────────────────────────────────────
@member_required
def my_profile(request, member):
    if request.method == 'POST':
        member.phone = request.POST.get('phone', member.phone)
        member.email = request.POST.get('email', member.email)
        member.address = request.POST.get('address', '')
        if 'profile_image' in request.FILES:
            member.profile_image = request.FILES['profile_image']
        member.save()
        messages.success(request, 'Profile updated!')
        return redirect('portal:profile')
    return render(request, 'portal/my_profile.html', {'member': member})
