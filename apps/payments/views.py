from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from apps.accounts.permissions import role_required, FRONT_DESK_ROLES
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta, date

from .models import Payment, Invoice, InvoiceItem, Receipt, InstallmentPlan, Installment, Refund, CashRegister
from apps.members.models import Member
from apps.memberships.models import MemberSubscription


# ── Revenue Dashboard ──────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def revenue_dashboard(request):
    today     = timezone.now().date()
    month_ago = today - timedelta(days=30)
    year_ago  = today - timedelta(days=365)

    payments = Payment.objects.filter(status='completed')

    stats = {
        'today_revenue':  payments.filter(payment_date=today).aggregate(t=Sum('net_amount'))['t'] or 0,
        'month_revenue':  payments.filter(payment_date__gte=month_ago).aggregate(t=Sum('net_amount'))['t'] or 0,
        'year_revenue':   payments.filter(payment_date__gte=year_ago).aggregate(t=Sum('net_amount'))['t'] or 0,
        'today_count':    payments.filter(payment_date=today).count(),
        'pending_count':  Payment.objects.filter(status='pending').count(),
        'overdue_invoices': Invoice.objects.filter(status='overdue').count(),
        'pending_refunds':  Refund.objects.filter(status='pending').count(),
    }

    # Monthly trend
    monthly = []
    for i in range(5, -1, -1):
        d = today.replace(day=1) - timedelta(days=i*30)
        rev = payments.filter(payment_date__year=d.year, payment_date__month=d.month).aggregate(t=Sum('net_amount'))['t'] or 0
        cnt = payments.filter(payment_date__year=d.year, payment_date__month=d.month).count()
        monthly.append({'label': d.strftime('%b'), 'revenue': float(rev), 'count': cnt})

    # Method breakdown
    method_stats = (payments.filter(payment_date__gte=month_ago)
                    .values('method').annotate(total=Sum('net_amount'), count=Count('id'))
                    .order_by('-total'))

    # Type breakdown
    type_stats = (payments.filter(payment_date__gte=month_ago)
                  .values('payment_type').annotate(total=Sum('net_amount'))
                  .order_by('-total'))

    # Recent payments
    recent = Payment.objects.select_related('member').order_by('-created_at')[:8]

    # Cash register today
    cash_register = CashRegister.objects.filter(date=today).first()

    return render(request, 'payments/dashboard.html', {
        'stats': stats, 'monthly': monthly,
        'method_stats': method_stats, 'type_stats': type_stats,
        'recent': recent, 'cash_register': cash_register,
        'today': today,
    })


# ── Payment List ───────────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def payment_list(request):
    payments = Payment.objects.select_related('member').order_by('-payment_date', '-created_at')
    q          = request.GET.get('q', '')
    date_from  = request.GET.get('from', '')
    date_to    = request.GET.get('to', '')
    method_f   = request.GET.get('method', '')
    status_f   = request.GET.get('status', '')
    type_f     = request.GET.get('type', '')

    if q:
        payments = payments.filter(Q(member__first_name__icontains=q)|Q(member__last_name__icontains=q)|Q(member__member_id__icontains=q)|Q(reference__icontains=q))
    if date_from: payments = payments.filter(payment_date__gte=date_from)
    if date_to:   payments = payments.filter(payment_date__lte=date_to)
    if method_f:  payments = payments.filter(method=method_f)
    if status_f:  payments = payments.filter(status=status_f)
    if type_f:    payments = payments.filter(payment_type=type_f)

    total_amount = payments.filter(status='completed').aggregate(t=Sum('net_amount'))['t'] or 0

    return render(request, 'payments/payment_list.html', {
        'payments': payments[:200], 'total': payments.count(),
        'total_amount': total_amount,
        'q': q, 'date_from': date_from, 'date_to': date_to,
        'method_f': method_f, 'status_f': status_f, 'type_f': type_f,
        'methods': Payment.Method.choices,
        'statuses': Payment.Status.choices,
        'types': Payment.PaymentType.choices,
    })


# ── New Payment ────────────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def payment_new(request):
    member_pk = request.GET.get('member')
    member    = Member.objects.filter(pk=member_pk).first() if member_pk else None

    if request.method == 'POST':
        try:
            m  = get_object_or_404(Member, pk=request.POST.get('member'))
            pay = Payment.objects.create(
                member       = m,
                payment_type = request.POST.get('payment_type', 'membership'),
                method       = request.POST.get('method', 'cash'),
                amount       = request.POST.get('amount', 0),
                discount     = request.POST.get('discount', 0),
                tax          = request.POST.get('tax', 0),
                reference    = request.POST.get('reference', ''),
                payment_date = request.POST.get('payment_date') or timezone.now().date(),
                notes        = request.POST.get('notes', ''),
                status       = 'completed',
                received_by  = request.user,
            )
            # Auto-create receipt
            Receipt.objects.create(payment=pay, issued_by=request.user)

            # Update cash register
            register, _ = CashRegister.objects.get_or_create(
                date=pay.payment_date,
                defaults={'opened_by': request.user, 'status': 'open'}
            )
            if pay.method == 'cash':
                register.total_cash_in = float(register.total_cash_in) + float(pay.net_amount)
                register.save(update_fields=['total_cash_in'])

            messages.success(request, f'Payment of {pay.net_amount} EGP recorded for {m.get_full_name()}!')
            return redirect('payments:detail', pk=pay.pk)
        except Exception as e:
            messages.error(request, f'Error: {e}')

    members = Member.objects.filter(status='active').order_by('first_name')
    subscriptions = MemberSubscription.objects.filter(status='active').select_related('member', 'plan') if not member else MemberSubscription.objects.filter(member=member, status='active').select_related('plan')

    return render(request, 'payments/payment_new.html', {
        'member': member, 'members': members,
        'subscriptions': subscriptions,
        'methods':  Payment.Method.choices,
        'types':    Payment.PaymentType.choices,
        'today':    timezone.now().date(),
    })


# ── Payment Detail ─────────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def payment_detail(request, pk):
    pay = get_object_or_404(Payment.objects.select_related('member', 'received_by', 'invoice'), pk=pk)
    receipt = getattr(pay, 'receipt', None)
    return render(request, 'payments/payment_detail.html', {'pay': pay, 'receipt': receipt})


# ── Pending Payments ───────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def pending_payments(request):
    payments = Payment.objects.filter(status='pending').select_related('member').order_by('-payment_date')
    invoices = Invoice.objects.filter(status__in=['sent','draft']).select_related('member').order_by('due_date')
    return render(request, 'payments/pending_payments.html', {
        'payments': payments, 'invoices': invoices,
        'p_count': payments.count(), 'i_count': invoices.count(),
    })


# ── Overdue Payments ───────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def overdue_payments(request):
    today    = timezone.now().date()
    invoices = Invoice.objects.filter(due_date__lt=today, status__in=['sent','partial']).select_related('member').order_by('due_date')
    installments = Installment.objects.filter(due_date__lt=today, status='pending').select_related('plan__member').order_by('due_date')

    for inv in invoices:
        if inv.status != 'overdue':
            inv.status = 'overdue'
            inv.save(update_fields=['status'])

    return render(request, 'payments/overdue_payments.html', {
        'invoices': invoices, 'installments': installments,
        'inv_count': invoices.count(), 'inst_count': installments.count(),
        'today': today,
    })


# ── Invoice List ───────────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def invoice_list(request):
    invoices = Invoice.objects.select_related('member').order_by('-issue_date')
    status_f = request.GET.get('status', '')
    q        = request.GET.get('q', '')
    if status_f: invoices = invoices.filter(status=status_f)
    if q:        invoices = invoices.filter(Q(member__first_name__icontains=q)|Q(member__last_name__icontains=q)|Q(invoice_number__icontains=q))

    stats = {
        'total':     invoices.aggregate(t=Sum('total'))['t'] or 0,
        'paid':      invoices.filter(status='paid').aggregate(t=Sum('total'))['t'] or 0,
        'overdue':   invoices.filter(status='overdue').count(),
        'draft':     invoices.filter(status='draft').count(),
    }
    return render(request, 'payments/invoice_list.html', {
        'invoices': invoices[:200], 'total': invoices.count(),
        'stats': stats, 'status_f': status_f, 'q': q,
        'statuses': Invoice.Status.choices,
    })


# ── New Invoice ────────────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def invoice_new(request):
    member_pk = request.GET.get('member')
    member    = Member.objects.filter(pk=member_pk).first() if member_pk else None

    if request.method == 'POST':
        try:
            m   = get_object_or_404(Member, pk=request.POST.get('member'))
            inv = Invoice.objects.create(
                member    = m,
                due_date  = request.POST.get('due_date'),
                subtotal  = request.POST.get('subtotal', 0),
                discount_amount = request.POST.get('discount_amount', 0),
                tax_amount= request.POST.get('tax_amount', 0),
                total     = request.POST.get('total', 0),
                notes     = request.POST.get('notes', ''),
                status    = request.POST.get('status', 'draft'),
                created_by= request.user,
            )
            # Create items
            descs  = request.POST.getlist('item_desc')
            qtys   = request.POST.getlist('item_qty')
            prices = request.POST.getlist('item_price')
            for d, qty, p in zip(descs, qtys, prices):
                if d.strip():
                    InvoiceItem.objects.create(invoice=inv, description=d, quantity=qty, unit_price=p)
            messages.success(request, f'Invoice {inv.invoice_number} created!')
            return redirect('payments:invoice_detail', pk=inv.pk)
        except Exception as e:
            messages.error(request, f'Error: {e}')

    members = Member.objects.filter(status='active').order_by('first_name')
    return render(request, 'payments/invoice_form.html', {
        'member': member, 'members': members,
        'today': timezone.now().date(),
    })


# ── Invoice Detail ─────────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def invoice_detail(request, pk):
    inv     = get_object_or_404(Invoice.objects.select_related('member','created_by').prefetch_related('items'), pk=pk)
    payments= Payment.objects.filter(invoice=inv).select_related('received_by')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'mark_paid':
            inv.status     = 'paid'
            inv.amount_paid= inv.total
            inv.save(update_fields=['status','amount_paid'])
            messages.success(request, 'Invoice marked as paid.')
        elif action == 'cancel':
            inv.status = 'cancelled'
            inv.save(update_fields=['status'])
            messages.info(request, 'Invoice cancelled.')
        return redirect('payments:invoice_detail', pk=pk)

    return render(request, 'payments/invoice_detail.html', {
        'inv': inv, 'payments': payments,
    })


# ── Receipts ───────────────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def receipt_list(request):
    receipts = Receipt.objects.select_related('payment__member','issued_by').order_by('-issued_at')
    q = request.GET.get('q', '')
    if q:
        receipts = receipts.filter(Q(payment__member__first_name__icontains=q)|Q(payment__member__last_name__icontains=q)|Q(receipt_number__icontains=q))
    return render(request, 'payments/receipt_list.html', {
        'receipts': receipts[:200], 'total': receipts.count(), 'q': q,
    })


@role_required(*FRONT_DESK_ROLES)
def receipt_detail(request, pk):
    receipt = get_object_or_404(Receipt.objects.select_related('payment__member','issued_by'), pk=pk)
    return render(request, 'payments/receipt_detail.html', {'receipt': receipt})


# ── Installments ───────────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def installment_list(request):
    plans = InstallmentPlan.objects.select_related('member').prefetch_related('installments').order_by('-created_at')
    status_f = request.GET.get('status', '')
    if status_f: plans = plans.filter(status=status_f)
    return render(request, 'payments/installment_list.html', {
        'plans': plans, 'total': plans.count(),
        'status_f': status_f, 'statuses': InstallmentPlan.Status.choices,
    })


@role_required(*FRONT_DESK_ROLES)
def installment_new(request):
    member_pk = request.GET.get('member')
    member    = Member.objects.filter(pk=member_pk).first() if member_pk else None

    if request.method == 'POST':
        try:
            m         = get_object_or_404(Member, pk=request.POST.get('member'))
            total     = float(request.POST.get('total_amount', 0))
            down      = float(request.POST.get('down_payment', 0))
            num       = int(request.POST.get('num_installments', 3))
            inst_amt  = round((total - down) / num, 2)
            start     = date.fromisoformat(request.POST.get('start_date'))

            plan = InstallmentPlan.objects.create(
                member=m, description=request.POST.get('description',''),
                total_amount=total, down_payment=down,
                num_installments=num, installment_amount=inst_amt,
                start_date=start, notes=request.POST.get('notes',''),
                created_by=request.user,
            )
            # Create installment records
            from dateutil.relativedelta import relativedelta
            for i in range(1, num + 1):
                due = start + relativedelta(months=i)
                Installment.objects.create(plan=plan, number=i, due_date=due, amount=inst_amt)

            messages.success(request, f'Installment plan created for {m.get_full_name()}!')
            return redirect('payments:installment_detail', pk=plan.pk)
        except Exception as e:
            messages.error(request, f'Error: {e}')

    members = Member.objects.filter(status='active').order_by('first_name')
    return render(request, 'payments/installment_form.html', {
        'member': member, 'members': members,
        'today': timezone.now().date(),
    })


@role_required(*FRONT_DESK_ROLES)
def installment_detail(request, pk):
    plan = get_object_or_404(InstallmentPlan.objects.select_related('member').prefetch_related('installments'), pk=pk)
    return render(request, 'payments/installment_detail.html', {'plan': plan})


@role_required(*FRONT_DESK_ROLES)
def installment_pay(request, pk, inst_pk):
    plan = get_object_or_404(InstallmentPlan, pk=pk)
    inst = get_object_or_404(Installment, pk=inst_pk, plan=plan)

    if request.method == 'POST':
        method = request.POST.get('method', 'cash')
        pay = Payment.objects.create(
            member=plan.member, payment_type='membership',
            method=method, amount=inst.amount,
            payment_date=timezone.now().date(),
            notes=f'Installment #{inst.number} — {plan.description}',
            status='completed', received_by=request.user,
        )
        Receipt.objects.create(payment=pay, issued_by=request.user)
        inst.status     = 'paid'
        inst.paid_date  = timezone.now().date()
        inst.paid_amount= inst.amount
        inst.payment    = pay
        inst.save()

        # Check if plan complete
        if not plan.installments.filter(status='pending').exists():
            plan.status = 'completed'
            plan.save(update_fields=['status'])

        messages.success(request, f'Installment #{inst.number} paid!')
        return redirect('payments:installment_detail', pk=pk)

    return render(request, 'payments/installment_pay.html', {
        'plan': plan, 'inst': inst,
        'methods': Payment.Method.choices,
    })


# ── Refunds ────────────────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def refund_list(request):
    refunds = Refund.objects.select_related('payment__member','requested_by').order_by('-requested_at')
    return render(request, 'payments/refund_list.html', {
        'refunds': refunds, 'total': refunds.count(),
    })


@role_required(*FRONT_DESK_ROLES)
def refund_new(request, payment_pk):
    pay = get_object_or_404(Payment, pk=payment_pk)

    if request.method == 'POST':
        refund = Refund.objects.create(
            payment=pay, member=pay.member,
            reason=request.POST.get('reason','other'),
            amount=request.POST.get('amount', pay.net_amount),
            notes=request.POST.get('notes',''),
            status='pending', requested_by=request.user,
        )
        pay.status = 'refunded'
        pay.save(update_fields=['status'])
        messages.success(request, 'Refund request submitted.')
        return redirect('payments:refunds')

    return render(request, 'payments/refund_form.html', {
        'pay': pay, 'reasons': Refund.Reason.choices,
    })


# ── Cash Register ──────────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def daily_cash_register(request):
    today    = timezone.now().date()
    register, created = CashRegister.objects.get_or_create(
        date=today,
        defaults={'opened_by': request.user, 'status': 'open'}
    )
    if created:
        messages.info(request, f'Cash register opened for {today}.')

    payments_today = Payment.objects.filter(payment_date=today, status='completed').select_related('member')
    method_totals  = payments_today.values('method').annotate(total=Sum('net_amount'), count=Count('id'))

    return render(request, 'payments/cash_register.html', {
        'register': register, 'today': today,
        'payments_today': payments_today,
        'method_totals': method_totals,
        'total_revenue': register.total_revenue,
        'cash_revenue':  register.cash_revenue,
    })


@role_required(*FRONT_DESK_ROLES)
def daily_closing(request):
    today    = timezone.now().date()
    register = get_object_or_404(CashRegister, date=today)

    if request.method == 'POST':
        register.closing_balance = request.POST.get('closing_balance', register.expected_closing)
        register.status          = 'closed'
        register.closed_by       = request.user
        register.closed_at       = timezone.now()
        register.notes           = request.POST.get('notes', '')
        register.save()
        messages.success(request, f'Cash register closed for {today}.')
        return redirect('payments:dashboard')

    return render(request, 'payments/daily_closing.html', {
        'register': register, 'today': today,
        'total_revenue': register.total_revenue,
        'cash_revenue':  register.cash_revenue,
        'expected_closing': register.expected_closing,
    })


# ── Payment Reports ────────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def payment_reports(request):
    today     = timezone.now().date()
    date_from = request.GET.get('from', str(today.replace(day=1)))
    date_to   = request.GET.get('to', str(today))

    payments = Payment.objects.filter(
        payment_date__gte=date_from, payment_date__lte=date_to,
        status='completed'
    )

    stats = {
        'total_revenue': payments.aggregate(t=Sum('net_amount'))['t'] or 0,
        'total_count':   payments.count(),
        'avg_payment':   payments.aggregate(a=Sum('net_amount'))['a'] or 0,
        'cash_total':    payments.filter(method='cash').aggregate(t=Sum('net_amount'))['t'] or 0,
        'card_total':    payments.filter(method='card').aggregate(t=Sum('net_amount'))['t'] or 0,
        'refunds_total': Payment.objects.filter(status='refunded', payment_date__gte=date_from, payment_date__lte=date_to).aggregate(t=Sum('net_amount'))['t'] or 0,
    }
    if payments.count() > 0:
        stats['avg_payment'] = round(float(stats['total_revenue']) / payments.count(), 2)

    type_breakdown = payments.values('payment_type').annotate(total=Sum('net_amount'), count=Count('id')).order_by('-total')
    method_breakdown = payments.values('method').annotate(total=Sum('net_amount'), count=Count('id')).order_by('-total')

    daily = (payments.values('payment_date')
             .annotate(total=Sum('net_amount'), count=Count('id'))
             .order_by('-payment_date')[:30])

    top_payers = (payments.values('member__first_name','member__last_name','member__pk','member__member_id')
                  .annotate(total=Sum('net_amount')).order_by('-total')[:10])

    return render(request, 'payments/reports.html', {
        'stats': stats, 'type_breakdown': type_breakdown,
        'method_breakdown': method_breakdown, 'daily': daily,
        'top_payers': top_payers,
        'date_from': date_from, 'date_to': date_to, 'today': today,
    })


# ── AJAX ───────────────────────────────────────────────────
@role_required(*FRONT_DESK_ROLES)
def ajax_member_info(request, pk):
    member = get_object_or_404(Member, pk=pk)
    sub    = MemberSubscription.objects.filter(member=member, status='active').select_related('plan').first()
    return JsonResponse({
        'name':        member.get_full_name(),
        'member_id':   member.member_id,
        'email':       member.email,
        'phone':       member.phone,
        'plan':        sub.plan.name if sub else None,
        'plan_price':  str(sub.plan.price) if sub else None,
        'amount_due':  str(sub.amount_due) if sub else None,
    })
