from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta

from .models import (
    MembershipCategory, MembershipPlan, MemberSubscription,
    Discount, Coupon, Offer, FamilyMembership, CorporateMembership,
    FamilyMember, CorporateEmployee,
)
from .forms import (
    MembershipCategoryForm, MembershipPlanForm, SubscriptionForm,
    RenewSubscriptionForm, UpgradeSubscriptionForm, TransferSubscriptionForm,
    FreezeSubscriptionForm, DiscountForm, CouponForm, OfferForm,
    FamilyMembershipForm, CorporateMembershipForm,
)
from apps.accounts.utils import log_activity
from apps.members.models import Member, MemberTimeline


def _log(request, action, desc):
    log_activity(request, request.user, action, desc)


def _timeline(member, event_type, title, desc='', user=None):
    MemberTimeline.objects.create(
        member=member, event_type=event_type,
        title=title, description=desc, created_by=user,
    )


def _apply_coupon(code, plan, original_price):
    """Try to apply a coupon code. Returns (discount_amount, coupon_obj, error_msg)."""
    try:
        coupon = Coupon.objects.get(code=code.upper(), is_active=True)
        if not coupon.is_valid():
            return 0, None, 'Coupon is expired or no longer valid.'
        plans = coupon.discount.applicable_plans.all()
        if plans.exists() and plan not in plans:
            return 0, None, 'This coupon is not applicable to the selected plan.'
        disc = coupon.discount.calculate(original_price)
        return disc, coupon, None
    except Coupon.DoesNotExist:
        return 0, None, 'Invalid coupon code.'


# ── Membership Plans ───────────────────────────────────────
@login_required
def plan_list(request):
    categories = MembershipCategory.objects.filter(is_active=True).prefetch_related('plans')
    all_plans  = MembershipPlan.objects.select_related('category').order_by('sort_order', 'price')

    q = request.GET.get('q', '')
    if q:
        all_plans = all_plans.filter(Q(name__icontains=q) | Q(description__icontains=q))

    plan_type = request.GET.get('type', '')
    if plan_type:
        all_plans = all_plans.filter(plan_type=plan_type)

    stats = {
        'total_plans':    MembershipPlan.objects.count(),
        'active_plans':   MembershipPlan.objects.filter(is_active=True).count(),
        'total_subs':     MemberSubscription.objects.filter(status='active').count(),
        'total_revenue':  MemberSubscription.objects.filter(
                              payment_status='paid'
                          ).aggregate(t=Sum('final_price'))['t'] or 0,
    }
    return render(request, 'memberships/plan_list.html', {
        'plans':        all_plans,
        'categories':   categories,
        'stats':        stats,
        'q':            q,
        'plan_type':    plan_type,
        'plan_types':   MembershipPlan.PlanType.choices,
    })


# ── Plan Categories ────────────────────────────────────────
@login_required
def category_list(request):
    categories = MembershipCategory.objects.annotate(
        plan_count=Count('plans')
    ).order_by('sort_order')
    if request.method == 'POST':
        form = MembershipCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added.')
            return redirect('memberships:categories')
    else:
        form = MembershipCategoryForm()
    return render(request, 'memberships/category_list.html', {
        'categories': categories, 'form': form,
    })


@login_required
def category_edit(request, pk):
    cat = get_object_or_404(MembershipCategory, pk=pk)
    if request.method == 'POST':
        form = MembershipCategoryForm(request.POST, instance=cat)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated.')
            return redirect('memberships:categories')
    else:
        form = MembershipCategoryForm(instance=cat)
    return render(request, 'memberships/category_edit.html', {'form': form, 'cat': cat})


@login_required
def category_delete(request, pk):
    cat = get_object_or_404(MembershipCategory, pk=pk)
    if request.method == 'POST':
        cat.delete()
        messages.success(request, 'Category deleted.')
        return redirect('memberships:categories')
    return render(request, 'memberships/confirm_action.html', {
        'title': 'Delete Category', 'object_name': cat.name,
        'back_url': 'memberships:categories',
        'warning': 'Plans in this category will be unassigned.',
    })


# ── Add / Edit Plan ────────────────────────────────────────
@login_required
def plan_add(request):
    if request.method == 'POST':
        form = MembershipPlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.created_by = request.user
            plan.save()
            _log(request, 'settings_change', f'Plan created: {plan.name}')
            messages.success(request, f'Plan "{plan.name}" created!')
            return redirect('memberships:plan_detail', pk=plan.pk)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = MembershipPlanForm()
    return render(request, 'memberships/plan_form.html', {
        'form': form, 'action': 'Add', 'page_title': 'Add Membership Plan',
    })


@login_required
def plan_edit(request, pk):
    plan = get_object_or_404(MembershipPlan, pk=pk)
    if request.method == 'POST':
        form = MembershipPlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            _log(request, 'settings_change', f'Plan updated: {plan.name}')
            messages.success(request, 'Plan updated.')
            return redirect('memberships:plan_detail', pk=pk)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = MembershipPlanForm(instance=plan)
    return render(request, 'memberships/plan_form.html', {
        'form': form, 'plan': plan,
        'action': 'Edit', 'page_title': f'Edit — {plan.name}',
    })


@login_required
def plan_detail(request, pk):
    plan = get_object_or_404(MembershipPlan, pk=pk)
    subs = MemberSubscription.objects.filter(plan=plan).select_related('member').order_by('-start_date')
    stats = {
        'active':   subs.filter(status='active').count(),
        'expired':  subs.filter(status='expired').count(),
        'frozen':   subs.filter(status='frozen').count(),
        'revenue':  subs.filter(payment_status='paid').aggregate(t=Sum('final_price'))['t'] or 0,
    }
    return render(request, 'memberships/plan_detail.html', {
        'plan': plan, 'subscriptions': subs[:20], 'stats': stats,
    })


@login_required
def plan_delete(request, pk):
    plan = get_object_or_404(MembershipPlan, pk=pk)
    if request.method == 'POST':
        if plan.subscriptions.filter(status='active').exists():
            messages.error(request, 'Cannot delete plan with active subscriptions.')
            return redirect('memberships:plan_detail', pk=pk)
        name = plan.name
        plan.delete()
        messages.success(request, f'Plan "{name}" deleted.')
        return redirect('memberships:plans')
    return render(request, 'memberships/confirm_action.html', {
        'title': 'Delete Plan', 'object_name': plan.name,
        'back_url': 'memberships:plans',
        'warning': 'This will delete the plan permanently. Active subscriptions must be ended first.',
    })


# ── Subscription Views ─────────────────────────────────────
def _get_sub_list(status_filter=None, extra_filter=None):
    qs = MemberSubscription.objects.select_related('member', 'plan').order_by('-start_date')
    if status_filter:
        qs = qs.filter(status=status_filter)
    if extra_filter:
        qs = qs.filter(**extra_filter)
    return qs


@login_required
def active_memberships(request):
    today = timezone.now().date()
    subs  = _get_sub_list('active')
    q     = request.GET.get('q', '')
    if q:
        subs = subs.filter(
            Q(member__first_name__icontains=q) | Q(member__last_name__icontains=q) |
            Q(member__member_id__icontains=q)  | Q(plan__name__icontains=q)
        )
    expiring_soon = subs.filter(end_date__lte=today + timedelta(days=7))
    return render(request, 'memberships/subscription_list.html', {
        'subscriptions': subs, 'status': 'Active', 'status_key': 'active',
        'expiring_soon': expiring_soon.count(), 'q': q,
        'icon': 'fa-circle-check', 'color': 'green',
    })


@login_required
def expired_memberships(request):
    subs = _get_sub_list('expired')
    q = request.GET.get('q', '')
    if q:
        subs = subs.filter(
            Q(member__first_name__icontains=q) | Q(member__last_name__icontains=q)
        )
    return render(request, 'memberships/subscription_list.html', {
        'subscriptions': subs, 'status': 'Expired', 'status_key': 'expired',
        'q': q, 'icon': 'fa-calendar-xmark', 'color': 'red',
    })


@login_required
def frozen_memberships(request):
    subs = _get_sub_list('frozen')
    return render(request, 'memberships/subscription_list.html', {
        'subscriptions': subs, 'status': 'Frozen', 'status_key': 'frozen',
        'icon': 'fa-snowflake', 'color': 'blue',
    })


@login_required
def cancelled_memberships(request):
    subs = _get_sub_list('cancelled')
    return render(request, 'memberships/subscription_list.html', {
        'subscriptions': subs, 'status': 'Cancelled', 'status_key': 'cancelled',
        'icon': 'fa-xmark', 'color': 'gray',
    })


@login_required
def pending_renewals(request):
    today = timezone.now().date()
    subs  = MemberSubscription.objects.filter(
        status='active', end_date__lte=today + timedelta(days=14)
    ).select_related('member', 'plan').order_by('end_date')
    return render(request, 'memberships/pending_renewals.html', {
        'subscriptions': subs, 'today': today,
    })


# ── Subscription CRUD ──────────────────────────────────────
@login_required
def subscription_add(request):
    member_pk = request.GET.get('member')
    initial   = {}
    if member_pk:
        initial['member']    = member_pk
        initial['start_date'] = timezone.now().date()

    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            sub = form.save(commit=False)
            sub.original_price = sub.plan.price + sub.plan.setup_fee
            sub.final_price    = sub.original_price

            # Apply coupon
            code = form.cleaned_data.get('coupon_code', '').strip()
            if code:
                disc, coupon_obj, err = _apply_coupon(code, sub.plan, float(sub.original_price))
                if err:
                    messages.warning(request, f'Coupon: {err}')
                else:
                    sub.discount_amount = disc
                    sub.final_price     = float(sub.original_price) - disc
                    sub.coupon          = coupon_obj
                    coupon_obj.times_used += 1
                    coupon_obj.save(update_fields=['times_used'])
                    messages.info(request, f'Coupon applied! Discount: {disc} EGP')

            sub.status     = MemberSubscription.Status.ACTIVE
            sub.created_by = request.user
            # Auto-set end_date from plan duration if not provided
            if not sub.end_date and sub.plan:
                sub.end_date = sub.start_date + timedelta(days=sub.plan.duration_days)
            sub.save()

            _timeline(sub.member, 'membership_new',
                      f'New membership: {sub.plan.name}',
                      f'Valid {sub.start_date} → {sub.end_date}',
                      user=request.user)
            _log(request, 'member_added', f'Subscription created for {sub.member.get_full_name()}')
            messages.success(request, f'Membership activated for {sub.member.get_full_name()}!')
            return redirect('memberships:subscription_detail', pk=sub.pk)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = SubscriptionForm(initial=initial)

    return render(request, 'memberships/subscription_form.html', {
        'form': form, 'action': 'Add', 'page_title': 'New Membership',
    })


@login_required
def subscription_detail(request, pk):
    sub = get_object_or_404(
        MemberSubscription.objects.select_related('member', 'plan', 'coupon', 'discount'),
        pk=pk
    )
    sub.check_and_update_status()
    return render(request, 'memberships/subscription_detail.html', {'sub': sub})


@login_required
def renew_membership(request, pk):
    sub = get_object_or_404(MemberSubscription, pk=pk)
    if request.method == 'POST':
        form = RenewSubscriptionForm(request.POST)
        if form.is_valid():
            cd       = form.cleaned_data
            plan     = cd['plan']
            original = float(plan.price)
            discount = 0
            coupon_obj = None

            code = cd.get('coupon_code', '').strip()
            if code:
                discount, coupon_obj, err = _apply_coupon(code, plan, original)
                if err:
                    messages.warning(request, f'Coupon: {err}')
                    discount = 0

            new_sub = MemberSubscription.objects.create(
                member          = sub.member,
                plan            = plan,
                status          = MemberSubscription.Status.ACTIVE,
                payment_status  = cd['payment_status'],
                start_date      = cd['start_date'],
                end_date        = cd['start_date'] + timedelta(days=plan.duration_days),
                original_price  = original,
                discount_amount = discount,
                final_price     = original - discount,
                amount_paid     = cd.get('amount_paid') or 0,
                auto_renew      = cd.get('auto_renew', False),
                coupon          = coupon_obj,
                created_by      = request.user,
                notes           = cd.get('notes', ''),
            )
            if coupon_obj:
                coupon_obj.times_used += 1
                coupon_obj.save(update_fields=['times_used'])

            _timeline(sub.member, 'membership_rnw',
                      f'Membership renewed: {plan.name}',
                      user=request.user)
            messages.success(request, 'Membership renewed successfully!')
            return redirect('memberships:subscription_detail', pk=new_sub.pk)
    else:
        form = RenewSubscriptionForm(initial={'plan': sub.plan})
    return render(request, 'memberships/subscription_renew.html', {
        'form': form, 'sub': sub,
    })


@login_required
def upgrade_membership(request, pk):
    sub = get_object_or_404(MemberSubscription, pk=pk)
    if request.method == 'POST':
        form = UpgradeSubscriptionForm(request.POST)
        if form.is_valid():
            cd       = form.cleaned_data
            new_plan = cd['new_plan']
            is_up    = float(new_plan.price) >= float(sub.plan.price)
            u_type   = 'upgrade' if is_up else 'downgrade'

            sub.previous_plan = sub.plan
            sub.plan          = new_plan
            sub.upgrade_type  = u_type
            sub.original_price = new_plan.price
            sub.final_price    = new_plan.price
            if cd.get('notes'):
                sub.notes = cd['notes']
            sub.save()

            _timeline(sub.member, 'membership_rnw',
                      f'Membership {u_type}d to {new_plan.name}',
                      user=request.user)
            messages.success(request, f'Membership {u_type}d to {new_plan.name}!')
            return redirect('memberships:subscription_detail', pk=pk)
    else:
        form = UpgradeSubscriptionForm(initial={'new_plan': sub.plan})
    return render(request, 'memberships/subscription_upgrade.html', {
        'form': form, 'sub': sub,
    })


@login_required
def transfer_membership(request, pk):
    sub = get_object_or_404(MemberSubscription, pk=pk)
    if request.method == 'POST':
        form = TransferSubscriptionForm(request.POST)
        if form.is_valid():
            target = form.cleaned_data['target_member']
            reason = form.cleaned_data['reason']
            old    = sub.member

            sub.member       = target
            sub.upgrade_type = 'transfer'
            sub.notes        = f'Transferred from {old.get_full_name()}: {reason}'
            sub.save()

            _timeline(old, 'membership_exp',
                      f'Membership transferred to {target.get_full_name()}',
                      user=request.user)
            _timeline(target, 'membership_new',
                      f'Membership transferred from {old.get_full_name()}',
                      user=request.user)
            messages.success(request, f'Membership transferred to {target.get_full_name()}!')
            return redirect('memberships:subscription_detail', pk=pk)
    else:
        form = TransferSubscriptionForm()
    return render(request, 'memberships/subscription_transfer.html', {
        'form': form, 'sub': sub,
    })


@login_required
def freeze_membership(request, pk):
    sub = get_object_or_404(MemberSubscription, pk=pk)
    if request.method == 'POST':
        form = FreezeSubscriptionForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            days_allowed = sub.plan.max_freeze_days - sub.freeze_days_used
            days_req     = (cd['freeze_end'] - cd['freeze_start']).days
            if days_req > days_allowed:
                messages.error(request, f'Only {days_allowed} freeze days remaining for this plan.')
            else:
                sub.freeze(cd['freeze_start'], cd['freeze_end'])
                _timeline(sub.member, 'frozen',
                          f'Membership frozen until {cd["freeze_end"]}',
                          cd.get('reason', ''), user=request.user)
                messages.success(request, 'Membership frozen.')
                return redirect('memberships:subscription_detail', pk=pk)
    else:
        form = FreezeSubscriptionForm()
    return render(request, 'memberships/subscription_freeze.html', {
        'form': form, 'sub': sub,
    })


@login_required
def cancel_membership(request, pk):
    sub = get_object_or_404(MemberSubscription, pk=pk)
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        sub.cancel(reason)
        _timeline(sub.member, 'membership_exp',
                  f'Membership cancelled: {sub.plan.name}',
                  reason, user=request.user)
        messages.success(request, 'Membership cancelled.')
        return redirect('memberships:active')
    return render(request, 'memberships/subscription_cancel.html', {'sub': sub})


# ── Family Memberships ─────────────────────────────────────
@login_required
def family_list(request):
    families = FamilyMembership.objects.select_related(
        'primary_member', 'plan'
    ).prefetch_related('family_members').order_by('-created_at')
    return render(request, 'memberships/family_list.html', {'families': families})


@login_required
def family_add(request):
    if request.method == 'POST':
        form = FamilyMembershipForm(request.POST)
        if form.is_valid():
            family = form.save()
            messages.success(request, f'Family membership "{family.name}" created!')
            return redirect('memberships:family_list')
    else:
        form = FamilyMembershipForm()
    return render(request, 'memberships/family_form.html', {
        'form': form, 'page_title': 'New Family Membership',
    })


# ── Corporate Memberships ──────────────────────────────────
@login_required
def corporate_list(request):
    companies = CorporateMembership.objects.select_related(
        'plan'
    ).annotate(emp_count=Count('employees')).order_by('-created_at')
    return render(request, 'memberships/corporate_list.html', {'companies': companies})


@login_required
def corporate_add(request):
    if request.method == 'POST':
        form = CorporateMembershipForm(request.POST)
        if form.is_valid():
            corp = form.save(commit=False)
            corp.created_by = request.user
            corp.save()
            messages.success(request, f'Corporate membership for {corp.company_name} created!')
            return redirect('memberships:corporate_list')
    else:
        form = CorporateMembershipForm()
    return render(request, 'memberships/corporate_form.html', {
        'form': form, 'page_title': 'New Corporate Membership',
    })


# ── Discounts ──────────────────────────────────────────────
@login_required
def discount_list(request):
    discounts = Discount.objects.prefetch_related('applicable_plans').order_by('-created_at')
    if request.method == 'POST':
        form = DiscountForm(request.POST)
        if form.is_valid():
            d = form.save(commit=False)
            d.created_by = request.user
            d.save()
            form.save_m2m()
            messages.success(request, f'Discount "{d.name}" created!')
            return redirect('memberships:discounts')
    else:
        form = DiscountForm()
    return render(request, 'memberships/discount_list.html', {
        'discounts': discounts, 'form': form,
    })


@login_required
def discount_edit(request, pk):
    d = get_object_or_404(Discount, pk=pk)
    if request.method == 'POST':
        form = DiscountForm(request.POST, instance=d)
        if form.is_valid():
            form.save()
            messages.success(request, 'Discount updated.')
            return redirect('memberships:discounts')
    else:
        form = DiscountForm(instance=d)
    return render(request, 'memberships/discount_edit.html', {'form': form, 'discount': d})


@login_required
def discount_delete(request, pk):
    d = get_object_or_404(Discount, pk=pk)
    if request.method == 'POST':
        d.delete()
        messages.success(request, 'Discount deleted.')
        return redirect('memberships:discounts')
    return render(request, 'memberships/confirm_action.html', {
        'title': 'Delete Discount', 'object_name': d.name,
        'back_url': 'memberships:discounts',
    })


# ── Coupons ────────────────────────────────────────────────
@login_required
def coupon_list(request):
    coupons = Coupon.objects.select_related('discount', 'member').order_by('-created_at')
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            c = form.save(commit=False)
            c.created_by = request.user
            c.save()
            messages.success(request, f'Coupon "{c.code}" created!')
            return redirect('memberships:coupons')
    else:
        form = CouponForm()
    return render(request, 'memberships/coupon_list.html', {
        'coupons': coupons, 'form': form,
    })


@login_required
def coupon_delete(request, pk):
    c = get_object_or_404(Coupon, pk=pk)
    if request.method == 'POST':
        c.delete()
        messages.success(request, 'Coupon deleted.')
        return redirect('memberships:coupons')
    return render(request, 'memberships/confirm_action.html', {
        'title': 'Delete Coupon', 'object_name': c.code,
        'back_url': 'memberships:coupons',
    })


# ── Offers ─────────────────────────────────────────────────
@login_required
def offer_list(request):
    offers = Offer.objects.prefetch_related('applicable_plans').order_by('-valid_from')
    if request.method == 'POST':
        form = OfferForm(request.POST, request.FILES)
        if form.is_valid():
            o = form.save(commit=False)
            o.created_by = request.user
            o.save()
            form.save_m2m()
            messages.success(request, f'Offer "{o.name}" created!')
            return redirect('memberships:offers')
    else:
        form = OfferForm()
    return render(request, 'memberships/offer_list.html', {
        'offers': offers, 'form': form,
    })


@login_required
def offer_edit(request, pk):
    o = get_object_or_404(Offer, pk=pk)
    if request.method == 'POST':
        form = OfferForm(request.POST, request.FILES, instance=o)
        if form.is_valid():
            form.save()
            messages.success(request, 'Offer updated.')
            return redirect('memberships:offers')
    else:
        form = OfferForm(instance=o)
    return render(request, 'memberships/offer_edit.html', {'form': form, 'offer': o})


@login_required
def offer_delete(request, pk):
    o = get_object_or_404(Offer, pk=pk)
    if request.method == 'POST':
        o.delete()
        messages.success(request, 'Offer deleted.')
        return redirect('memberships:offers')
    return render(request, 'memberships/confirm_action.html', {
        'title': 'Delete Offer', 'object_name': o.name,
        'back_url': 'memberships:offers',
    })


# ── Statistics ─────────────────────────────────────────────
@login_required
def statistics(request):
    today    = timezone.now().date()
    month_ago = today - timedelta(days=30)

    stats = {
        'total_active':     MemberSubscription.objects.filter(status='active').count(),
        'total_expired':    MemberSubscription.objects.filter(status='expired').count(),
        'total_frozen':     MemberSubscription.objects.filter(status='frozen').count(),
        'total_cancelled':  MemberSubscription.objects.filter(status='cancelled').count(),
        'expiring_7days':   MemberSubscription.objects.filter(
                                status='active',
                                end_date__lte=today + timedelta(days=7),
                                end_date__gte=today
                            ).count(),
        'new_this_month':   MemberSubscription.objects.filter(
                                created_at__date__gte=month_ago
                            ).count(),
        'total_revenue':    MemberSubscription.objects.filter(
                                payment_status='paid'
                            ).aggregate(t=Sum('final_price'))['t'] or 0,
        'avg_price':        MembershipPlan.objects.filter(
                                is_active=True
                            ).aggregate(a=Avg('price'))['a'] or 0,
        'pending_payment':  MemberSubscription.objects.filter(
                                payment_status='unpaid', status='active'
                            ).count(),
        'total_discount':   MemberSubscription.objects.aggregate(
                                t=Sum('discount_amount')
                            )['t'] or 0,
    }

    # Plan breakdown
    plan_stats = MembershipPlan.objects.annotate(
        sub_count=Count('subscriptions', filter=Q(subscriptions__status='active')),
        revenue=Sum('subscriptions__final_price',
                    filter=Q(subscriptions__payment_status='paid')),
    ).filter(is_active=True).order_by('-sub_count')

    # Monthly trend (last 6 months)
    monthly_data = []
    for i in range(5, -1, -1):
        d     = today.replace(day=1) - timedelta(days=i*30)
        label = d.strftime('%b %Y')
        count = MemberSubscription.objects.filter(
            created_at__year=d.year, created_at__month=d.month
        ).count()
        rev = MemberSubscription.objects.filter(
            created_at__year=d.year, created_at__month=d.month,
            payment_status='paid'
        ).aggregate(t=Sum('final_price'))['t'] or 0
        monthly_data.append({'label': label, 'count': count, 'revenue': float(rev)})

    return render(request, 'memberships/statistics.html', {
        'stats': stats, 'plan_stats': plan_stats,
        'monthly_data': monthly_data, 'today': today,
    })
