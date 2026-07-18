from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Q

from apps.accounts.permissions import role_required, ADMIN_ROLES
from .models import Account, JournalEntry, JournalLine, Income, Expense, Budget, TaxRecord


def _date_range(request):
    today = date.today()
    date_from = request.GET.get('from', str(today.replace(day=1)))
    date_to   = request.GET.get('to', str(today))
    return date_from, date_to, today


# ── 1. Income ───────────────────────────────────────────────
@role_required(*ADMIN_ROLES)
def income_list(request):
    date_from, date_to, today = _date_range(request)
    income = Income.objects.filter(date__gte=date_from, date__lte=date_to).select_related('account')

    stats = {
        'total': income.aggregate(t=Sum('amount'))['t'] or 0,
        'count': income.count(),
    }
    by_category = income.values('category').annotate(total=Sum('amount')).order_by('-total')

    return render(request, 'finance/income_list.html', {
        'income': income.order_by('-date'), 'stats': stats, 'by_category': by_category,
        'date_from': date_from, 'date_to': date_to,
    })


@role_required(*ADMIN_ROLES)
def income_new(request):
    if request.method == 'POST':
        acc_pk = request.POST.get('account')
        Income.objects.create(
            date=request.POST.get('date'), category=request.POST.get('category','other'),
            description=request.POST.get('description'), amount=float(request.POST.get('amount',0)),
            account=Account.objects.filter(pk=acc_pk).first() if acc_pk else None,
            recorded_by=request.user,
        )
        messages.success(request, 'Income recorded!')
        return redirect('finance:income')
    return render(request, 'finance/income_form.html', {
        'categories': Income.Category.choices,
        'accounts': Account.objects.filter(account_type='income', is_active=True),
        'today': date.today(),
    })


# ── 2. Expenses ───────────────────────────────────────────────
@role_required(*ADMIN_ROLES)
def expenses_list(request):
    date_from, date_to, today = _date_range(request)
    expenses = Expense.objects.filter(date__gte=date_from, date__lte=date_to).select_related('account')

    stats = {
        'total': expenses.aggregate(t=Sum('amount'))['t'] or 0,
        'count': expenses.count(),
    }
    by_category = expenses.values('category').annotate(total=Sum('amount')).order_by('-total')

    return render(request, 'finance/expenses_list.html', {
        'expenses': expenses.order_by('-date'), 'stats': stats, 'by_category': by_category,
        'date_from': date_from, 'date_to': date_to,
    })


@role_required(*ADMIN_ROLES)
def expense_new(request):
    if request.method == 'POST':
        acc_pk = request.POST.get('account')
        Expense.objects.create(
            date=request.POST.get('date'), category=request.POST.get('category','other'),
            description=request.POST.get('description'), amount=float(request.POST.get('amount',0)),
            vendor=request.POST.get('vendor',''),
            account=Account.objects.filter(pk=acc_pk).first() if acc_pk else None,
            recorded_by=request.user,
        )
        messages.success(request, 'Expense recorded!')
        return redirect('finance:expenses')
    return render(request, 'finance/expense_form.html', {
        'categories': Expense.Category.choices,
        'accounts': Account.objects.filter(account_type='expense', is_active=True),
        'today': date.today(),
    })


# ── 3. Transactions (unified income + expense feed) ──────────
@role_required(*ADMIN_ROLES)
def transactions(request):
    date_from, date_to, today = _date_range(request)
    income = list(Income.objects.filter(date__gte=date_from, date__lte=date_to).values('date','description','amount','category'))
    for i in income: i['kind'] = 'income'
    expenses = list(Expense.objects.filter(date__gte=date_from, date__lte=date_to).values('date','description','amount','category'))
    for e in expenses: e['kind'] = 'expense'

    combined = sorted(income + expenses, key=lambda x: x['date'], reverse=True)

    return render(request, 'finance/transactions.html', {
        'combined': combined, 'date_from': date_from, 'date_to': date_to,
    })


# ── 4. Accounts (Chart of Accounts) ───────────────────────────
@role_required(*ADMIN_ROLES)
def accounts_list(request):
    accounts = Account.objects.filter(is_active=True).order_by('code')
    return render(request, 'finance/accounts_list.html', {'accounts': accounts})


@role_required(*ADMIN_ROLES)
def account_new(request):
    if request.method == 'POST':
        Account.objects.create(
            code=request.POST.get('code'), name=request.POST.get('name'),
            account_type=request.POST.get('account_type','expense'),
            description=request.POST.get('description',''),
        )
        messages.success(request, 'Account created!')
        return redirect('finance:accounts')
    return render(request, 'finance/account_form.html', {
        'account_types': Account.AccountType.choices,
    })


# ── 5. Cash Flow ───────────────────────────────────────────────
@role_required(*ADMIN_ROLES)
def cash_flow(request):
    today = date.today()
    monthly = []
    for i in range(5, -1, -1):
        d = today.replace(day=1) - timedelta(days=i*30)
        inc = Income.objects.filter(date__year=d.year, date__month=d.month).aggregate(t=Sum('amount'))['t'] or 0
        exp = Expense.objects.filter(date__year=d.year, date__month=d.month).aggregate(t=Sum('amount'))['t'] or 0
        monthly.append({'label': d.strftime('%b'), 'income': float(inc), 'expense': float(exp), 'net': float(inc)-float(exp)})

    total_in  = sum(m['income'] for m in monthly)
    total_out = sum(m['expense'] for m in monthly)

    return render(request, 'finance/cash_flow.html', {
        'monthly': monthly, 'total_in': total_in, 'total_out': total_out, 'net': total_in - total_out,
    })


# ── 6. Budget ───────────────────────────────────────────────────
@role_required(*ADMIN_ROLES)
def budget_list(request):
    budgets = Budget.objects.order_by('-start_date')
    return render(request, 'finance/budget_list.html', {'budgets': budgets})


@role_required(*ADMIN_ROLES)
def budget_new(request):
    if request.method == 'POST':
        Budget.objects.create(
            name=request.POST.get('name'), category=request.POST.get('category'),
            period=request.POST.get('period','monthly'),
            allocated_amount=float(request.POST.get('allocated_amount',0)),
            start_date=request.POST.get('start_date'), end_date=request.POST.get('end_date'),
        )
        messages.success(request, 'Budget created!')
        return redirect('finance:budget')
    return render(request, 'finance/budget_form.html', {
        'categories': Expense.Category.choices, 'periods': Budget.Period.choices,
        'today': date.today(),
    })


# ── 7. Taxes ─────────────────────────────────────────────────────
@role_required(*ADMIN_ROLES)
def taxes_list(request):
    taxes = TaxRecord.objects.order_by('-period_end')
    stats = {
        'total_due':  taxes.filter(status='pending').aggregate(t=Sum('tax_due'))['t'] or 0,
        'total_paid': taxes.filter(status='paid').aggregate(t=Sum('tax_due'))['t'] or 0,
    }
    return render(request, 'finance/taxes_list.html', {'taxes': taxes, 'stats': stats})


@role_required(*ADMIN_ROLES)
def tax_new(request):
    if request.method == 'POST':
        taxable = float(request.POST.get('taxable_amount', 0))
        rate = float(request.POST.get('tax_rate', 14))
        TaxRecord.objects.create(
            tax_type=request.POST.get('tax_type','vat'),
            period_start=request.POST.get('period_start'), period_end=request.POST.get('period_end'),
            taxable_amount=taxable, tax_rate=rate, tax_due=taxable * rate / 100,
        )
        messages.success(request, 'Tax record created!')
        return redirect('finance:taxes')
    return render(request, 'finance/tax_form.html', {
        'tax_types': TaxRecord.TaxType.choices,
    })


# ── 8. Financial Statements ────────────────────────────────────
@role_required(*ADMIN_ROLES)
def financial_statements(request):
    date_from, date_to, today = _date_range(request)

    total_income  = Income.objects.filter(date__gte=date_from, date__lte=date_to).aggregate(t=Sum('amount'))['t'] or 0
    total_expense = Expense.objects.filter(date__gte=date_from, date__lte=date_to).aggregate(t=Sum('amount'))['t'] or 0
    net_income = float(total_income) - float(total_expense)

    assets      = Account.objects.filter(account_type='asset', is_active=True)
    liabilities = Account.objects.filter(account_type='liability', is_active=True)
    equity      = Account.objects.filter(account_type='equity', is_active=True)

    total_assets = sum(a.balance for a in assets)
    total_liabilities = sum(l.balance for l in liabilities)
    total_equity = sum(e.balance for e in equity)

    return render(request, 'finance/statements.html', {
        'total_income': total_income, 'total_expense': total_expense, 'net_income': net_income,
        'assets': assets, 'liabilities': liabilities, 'equity': equity,
        'total_assets': total_assets, 'total_liabilities': total_liabilities, 'total_equity': total_equity,
        'date_from': date_from, 'date_to': date_to,
    })


# ── 9. Journal Entries ──────────────────────────────────────────
@role_required(*ADMIN_ROLES)
def journal_entries(request):
    entries = JournalEntry.objects.order_by('-date','-id')
    return render(request, 'finance/journal_list.html', {'entries': entries})


@role_required(*ADMIN_ROLES)
def journal_new(request):
    if request.method == 'POST':
        entry = JournalEntry.objects.create(
            date=request.POST.get('date'), description=request.POST.get('description'),
            reference=request.POST.get('reference',''), created_by=request.user,
        )
        account_ids = request.POST.getlist('account')
        debits      = request.POST.getlist('debit')
        credits     = request.POST.getlist('credit')
        for acc_id, debit, credit in zip(account_ids, debits, credits):
            if acc_id:
                JournalLine.objects.create(
                    entry=entry, account_id=acc_id,
                    debit=float(debit or 0), credit=float(credit or 0),
                )
        messages.success(request, f'{entry.entry_number} created!')
        return redirect('finance:journal_detail', pk=entry.pk)
    return render(request, 'finance/journal_form.html', {
        'accounts': Account.objects.filter(is_active=True).order_by('code'),
        'today': date.today(),
    })


@role_required(*ADMIN_ROLES)
def journal_detail(request, pk):
    entry = get_object_or_404(JournalEntry.objects.prefetch_related('lines__account'), pk=pk)
    return render(request, 'finance/journal_detail.html', {'entry': entry})


# ── 10. General Ledger ───────────────────────────────────────────
@role_required(*ADMIN_ROLES)
def general_ledger(request):
    accounts = Account.objects.filter(is_active=True).order_by('code')
    account_pk = request.GET.get('account')
    selected_account = Account.objects.filter(pk=account_pk).first() if account_pk else accounts.first()

    lines = JournalLine.objects.filter(account=selected_account).select_related('entry').order_by('entry__date') if selected_account else []

    running_balance = 0
    ledger_rows = []
    for line in lines:
        if selected_account.account_type in ('asset', 'expense'):
            running_balance += float(line.debit) - float(line.credit)
        else:
            running_balance += float(line.credit) - float(line.debit)
        ledger_rows.append({'line': line, 'balance': running_balance})

    return render(request, 'finance/ledger.html', {
        'accounts': accounts, 'selected_account': selected_account, 'ledger_rows': ledger_rows,
    })
