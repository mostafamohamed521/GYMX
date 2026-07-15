from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone

from apps.accounts.permissions import role_required, FRONT_DESK_ROLES
from .models import (
    Lead, FollowUp, CallLog, Meeting, Feedback, Complaint, Suggestion,
    LoyaltyTier, LoyaltyAccount, LoyaltyTransaction, Referral, Campaign,
)
from apps.members.models import Member


# ── 1. Leads ────────────────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def leads_list(request):
    leads = Lead.objects.select_related('assigned_to').order_by('-created_at')
    status_f = request.GET.get('status','')
    q        = request.GET.get('q','')
    if status_f: leads = leads.filter(status=status_f)
    if q: leads = leads.filter(Q(first_name__icontains=q)|Q(last_name__icontains=q)|Q(phone__icontains=q))

    stats = {
        'total':     Lead.objects.count(),
        'new':       Lead.objects.filter(status='new').count(),
        'qualified': Lead.objects.filter(status='qualified').count(),
        'converted': Lead.objects.filter(status='converted').count(),
    }
    return render(request, 'crm/leads_list.html', {
        'leads': leads, 'stats': stats, 'status_f': status_f, 'q': q,
        'statuses': Lead.Status.choices,
    })


@role_required(*FRONT_DESK_ROLES)
def lead_new(request):
    if request.method == 'POST':
        Lead.objects.create(
            first_name=request.POST.get('first_name'), last_name=request.POST.get('last_name'),
            phone=request.POST.get('phone'), email=request.POST.get('email',''),
            source=request.POST.get('source','walk_in'), interest=request.POST.get('interest',''),
            assigned_to=request.user, notes=request.POST.get('notes',''),
        )
        messages.success(request, 'Lead added!')
        return redirect('crm:leads')
    return render(request, 'crm/lead_form.html', {'sources': Lead.Source.choices})


@role_required(*FRONT_DESK_ROLES)
def lead_detail(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == 'POST':
        lead.status = request.POST.get('status', lead.status)
        lead.notes  = request.POST.get('notes', lead.notes)
        lead.save()
        messages.success(request, 'Lead updated.')
        return redirect('crm:lead_detail', pk=pk)
    follow_ups = lead.follow_ups.all()
    calls      = lead.calls.all()
    return render(request, 'crm/lead_detail.html', {
        'lead': lead, 'follow_ups': follow_ups, 'calls': calls,
        'statuses': Lead.Status.choices,
    })


@role_required(*FRONT_DESK_ROLES)
def lead_convert(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == 'POST':
        member = Member.objects.create(
            first_name=lead.first_name, last_name=lead.last_name,
            phone=lead.phone, email=lead.email, status='active',
        )
        lead.status = 'converted'
        lead.converted_member = member
        lead.save()
        messages.success(request, f'{lead.get_full_name()} converted to member!')
        return redirect('members:detail', pk=member.pk)
    return redirect('crm:lead_detail', pk=pk)


# ── 2. Prospects (qualified leads not yet converted) ────────
@role_required(*FRONT_DESK_ROLES)
def prospects(request):
    prospect_list = Lead.objects.filter(status='qualified').select_related('assigned_to').order_by('-created_at')
    return render(request, 'crm/prospects.html', {'prospect_list': prospect_list})


# ── 3. Follow-Ups ────────────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def follow_ups(request):
    today = date.today()
    if request.method == 'POST':
        lead = get_object_or_404(Lead, pk=request.POST.get('lead'))
        FollowUp.objects.create(
            lead=lead, scheduled_date=request.POST.get('scheduled_date'),
            scheduled_time=request.POST.get('scheduled_time','10:00'),
            notes=request.POST.get('notes',''), assigned_to=request.user,
        )
        messages.success(request, 'Follow-up scheduled.')
        return redirect('crm:follow_ups')

    followups = FollowUp.objects.select_related('lead').order_by('scheduled_date','scheduled_time')
    leads = Lead.objects.exclude(status__in=['converted','lost'])
    stats = {
        'pending': FollowUp.objects.filter(status='pending').count(),
        'today':   FollowUp.objects.filter(scheduled_date=today).count(),
        'overdue': FollowUp.objects.filter(status='pending', scheduled_date__lt=today).count(),
    }
    return render(request, 'crm/follow_ups.html', {
        'followups': followups, 'leads': leads, 'stats': stats, 'today': today,
    })


@role_required(*FRONT_DESK_ROLES)
def follow_up_complete(request, pk):
    fu = get_object_or_404(FollowUp, pk=pk)
    fu.status = 'done'
    fu.completed_at = timezone.now()
    fu.save()
    messages.success(request, 'Follow-up marked as done.')
    return redirect('crm:follow_ups')


# ── 4. Call Logs ─────────────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def call_logs(request):
    if request.method == 'POST':
        lead_pk   = request.POST.get('lead')
        member_pk = request.POST.get('member')
        CallLog.objects.create(
            lead=Lead.objects.filter(pk=lead_pk).first() if lead_pk else None,
            member=Member.objects.filter(pk=member_pk).first() if member_pk else None,
            direction=request.POST.get('direction','outbound'),
            outcome=request.POST.get('outcome','answered'),
            duration_min=int(request.POST.get('duration_min',0)),
            notes=request.POST.get('notes',''), called_by=request.user,
        )
        messages.success(request, 'Call logged.')
        return redirect('crm:calls')

    calls = CallLog.objects.select_related('lead','member','called_by').order_by('-called_at')[:100]
    leads = Lead.objects.exclude(status__in=['converted','lost'])
    members = Member.objects.filter(status='active').order_by('first_name')
    return render(request, 'crm/call_logs.html', {
        'calls': calls, 'leads': leads, 'members': members,
        'directions': CallLog.Direction.choices, 'outcomes': CallLog.Outcome.choices,
    })


# ── 5. Meetings ───────────────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def meetings(request):
    if request.method == 'POST':
        lead_pk   = request.POST.get('lead')
        member_pk = request.POST.get('member')
        Meeting.objects.create(
            lead=Lead.objects.filter(pk=lead_pk).first() if lead_pk else None,
            member=Member.objects.filter(pk=member_pk).first() if member_pk else None,
            title=request.POST.get('title'), date=request.POST.get('date'),
            start_time=request.POST.get('start_time'), end_time=request.POST.get('end_time'),
            location=request.POST.get('location',''), assigned_to=request.user,
        )
        messages.success(request, 'Meeting scheduled.')
        return redirect('crm:meetings')

    meeting_list = Meeting.objects.select_related('lead','member').order_by('-date')
    leads   = Lead.objects.exclude(status__in=['converted','lost'])
    members = Member.objects.filter(status='active').order_by('first_name')
    return render(request, 'crm/meetings.html', {
        'meeting_list': meeting_list, 'leads': leads, 'members': members, 'today': date.today(),
    })


# ── 6. Customer Feedback ──────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def feedback_list(request):
    feedback = Feedback.objects.select_related('member').order_by('-submitted_at')
    stats = {
        'total': feedback.count(),
        'avg_rating': feedback.aggregate(a=Avg('rating'))['a'] or 0,
    }
    return render(request, 'crm/feedback_list.html', {'feedback': feedback, 'stats': stats})


# ── 7. Complaints ─────────────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def complaints(request):
    if request.method == 'POST':
        member_pk = request.POST.get('member')
        Complaint.objects.create(
            member=Member.objects.filter(pk=member_pk).first() if member_pk else None,
            subject=request.POST.get('subject'), description=request.POST.get('description'),
            priority=request.POST.get('priority','medium'), assigned_to=request.user,
        )
        messages.success(request, 'Complaint logged.')
        return redirect('crm:complaints')

    complaint_list = Complaint.objects.select_related('member','assigned_to').order_by('-created_at')
    stats = {
        'open':   Complaint.objects.filter(status='open').count(),
        'urgent': Complaint.objects.filter(priority='urgent').count(),
        'resolved': Complaint.objects.filter(status='resolved').count(),
    }
    members = Member.objects.filter(status='active').order_by('first_name')
    return render(request, 'crm/complaints.html', {
        'complaint_list': complaint_list, 'stats': stats, 'members': members,
        'priorities': Complaint.Priority.choices,
    })


@role_required(*FRONT_DESK_ROLES)
def complaint_detail(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)
    if request.method == 'POST':
        complaint.status = request.POST.get('status', complaint.status)
        complaint.resolution = request.POST.get('resolution','')
        if complaint.status == 'resolved' and not complaint.resolved_at:
            complaint.resolved_at = timezone.now()
        complaint.save()
        messages.success(request, 'Complaint updated.')
        return redirect('crm:complaint_detail', pk=pk)
    return render(request, 'crm/complaint_detail.html', {
        'complaint': complaint, 'statuses': Complaint.Status.choices,
    })


# ── 8. Suggestions ────────────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def suggestions(request):
    suggestion_list = Suggestion.objects.select_related('member').order_by('-votes','-created_at')
    return render(request, 'crm/suggestions.html', {'suggestion_list': suggestion_list})


@role_required(*FRONT_DESK_ROLES)
def suggestion_vote(request, pk):
    s = get_object_or_404(Suggestion, pk=pk)
    s.votes += 1
    s.save(update_fields=['votes'])
    return redirect('crm:suggestions')


# ── 9. Loyalty Program ────────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def loyalty_program(request):
    accounts = LoyaltyAccount.objects.select_related('member','tier').order_by('-points')
    tiers    = LoyaltyTier.objects.all()
    stats = {
        'total_members': accounts.count(),
        'total_points':  accounts.aggregate(t=Sum('points'))['t'] or 0,
    }
    return render(request, 'crm/loyalty.html', {'accounts': accounts, 'tiers': tiers, 'stats': stats})


@role_required(*FRONT_DESK_ROLES)
def loyalty_add_points(request, pk):
    account = get_object_or_404(LoyaltyAccount, pk=pk)
    if request.method == 'POST':
        points = int(request.POST.get('points', 0))
        account.points += points
        # Auto-update tier
        tier = LoyaltyTier.objects.filter(min_points__lte=account.points).order_by('-min_points').first()
        account.tier = tier
        account.save()
        LoyaltyTransaction.objects.create(account=account, tx_type='earned', points=points, reason=request.POST.get('reason',''))
        messages.success(request, f'{points} points added.')
    return redirect('crm:loyalty')


# ── 10. Referral Program ──────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def referral_program(request):
    if request.method == 'POST':
        referrer = get_object_or_404(Member, pk=request.POST.get('referrer'))
        Referral.objects.create(
            referrer=referrer, referred_name=request.POST.get('referred_name'),
            referred_phone=request.POST.get('referred_phone',''),
            reward_points=int(request.POST.get('reward_points',100)),
        )
        messages.success(request, 'Referral recorded.')
        return redirect('crm:referrals')

    referral_list = Referral.objects.select_related('referrer','referred_member').order_by('-created_at')
    members = Member.objects.filter(status='active').order_by('first_name')
    stats = {
        'total':     referral_list.count(),
        'converted': referral_list.filter(status='converted').count(),
    }
    return render(request, 'crm/referrals.html', {
        'referral_list': referral_list, 'members': members, 'stats': stats,
    })


# ── 11. Campaigns ─────────────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def campaigns(request):
    campaign_list = Campaign.objects.order_by('-created_at')
    stats = {
        'total': Campaign.objects.count(),
        'sent':  Campaign.objects.filter(status='sent').count(),
    }
    return render(request, 'crm/campaigns.html', {'campaign_list': campaign_list, 'stats': stats})


@role_required(*FRONT_DESK_ROLES)
def campaign_new(request):
    if request.method == 'POST':
        Campaign.objects.create(
            name=request.POST.get('name'), channel=request.POST.get('channel','email'),
            subject=request.POST.get('subject',''), message=request.POST.get('message'),
            target_audience=request.POST.get('target_audience',''),
            status=request.POST.get('status','draft'),
            scheduled_at=request.POST.get('scheduled_at') or None,
            created_by=request.user,
        )
        messages.success(request, 'Campaign created!')
        return redirect('crm:campaigns')
    return render(request, 'crm/campaign_form.html', {
        'channels': Campaign.Channel.choices, 'statuses': Campaign.Status.choices,
    })
