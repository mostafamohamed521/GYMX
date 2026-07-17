from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Count, Avg, Q

from apps.accounts.permissions import role_required, ADMIN_ROLES
from .models import SavedReport, ExportLog
from apps.members.models import Member
from apps.memberships.models import MemberSubscription
from apps.attendance.models import AttendanceRecord
from apps.payments.models import Payment, Invoice
from apps.coaches.models import Coach
from apps.hr.models import Employee, Payroll
from apps.inventory.models import Product
from apps.pos.models import Sale


def _date_range(request):
    today = date.today()
    date_from = request.GET.get('from', str(today.replace(day=1)))
    date_to   = request.GET.get('to', str(today))
    return date_from, date_to, today


# ── 1. Analytics Dashboard ─────────────────────────────────
@role_required(*ADMIN_ROLES)
def analytics_dashboard(request):
    today     = date.today()
    month_ago = today - timedelta(days=30)

    stats = {
        'total_members':   Member.objects.count(),
        'active_members':  Member.objects.filter(status='active').count(),
        'revenue_30d':      Payment.objects.filter(status='completed', payment_date__gte=month_ago).aggregate(t=Sum('net_amount'))['t'] or 0,
        'pos_revenue_30d':  Sale.objects.filter(status='completed', created_at__date__gte=month_ago).aggregate(t=Sum('total'))['t'] or 0,
        'attendance_30d':   AttendanceRecord.objects.filter(date__gte=month_ago).count(),
        'active_coaches':   Coach.objects.filter(status='active').count(),
        'active_employees': Employee.objects.filter(status='active').count(),
        'low_stock':        sum(1 for p in Product.objects.filter(is_active=True) if p.is_low_stock),
    }

    monthly = []
    for i in range(5, -1, -1):
        d = today.replace(day=1) - timedelta(days=i*30)
        rev = Payment.objects.filter(status='completed', payment_date__year=d.year, payment_date__month=d.month).aggregate(t=Sum('net_amount'))['t'] or 0
        members = Member.objects.filter(created_at__year=d.year, created_at__month=d.month).count()
        monthly.append({'label': d.strftime('%b'), 'revenue': float(rev), 'members': members})

    return render(request, 'reports/analytics_dashboard.html', {
        'stats': stats, 'monthly': monthly, 'today': today,
    })


# ── 2. Revenue Reports ─────────────────────────────────────
@role_required(*ADMIN_ROLES)
def revenue_reports(request):
    date_from, date_to, today = _date_range(request)
    payments = Payment.objects.filter(status='completed', payment_date__gte=date_from, payment_date__lte=date_to)

    stats = {
        'total':    payments.aggregate(t=Sum('net_amount'))['t'] or 0,
        'count':    payments.count(),
        'avg':      payments.aggregate(a=Avg('net_amount'))['a'] or 0,
    }
    by_type   = payments.values('payment_type').annotate(total=Sum('net_amount'), count=Count('id')).order_by('-total')
    by_method = payments.values('method').annotate(total=Sum('net_amount'), count=Count('id')).order_by('-total')

    daily = payments.values('payment_date').annotate(total=Sum('net_amount')).order_by('payment_date')

    return render(request, 'reports/revenue_reports.html', {
        'stats': stats, 'by_type': by_type, 'by_method': by_method, 'daily': daily,
        'date_from': date_from, 'date_to': date_to,
    })


# ── 3. Membership Reports ──────────────────────────────────
@role_required(*ADMIN_ROLES)
def membership_reports(request):
    today = date.today()
    subs = MemberSubscription.objects.select_related('plan', 'member')

    stats = {
        'total':    subs.count(),
        'active':   subs.filter(status='active').count(),
        'expired':  subs.filter(status='expired').count(),
        'expiring_soon': subs.filter(status='active', end_date__lte=today+timedelta(days=7), end_date__gte=today).count(),
    }
    by_plan = subs.values('plan__name').annotate(count=Count('id')).order_by('-count')
    member_status = Member.objects.values('status').annotate(count=Count('id')).order_by('-count')

    return render(request, 'reports/membership_reports.html', {
        'stats': stats, 'by_plan': by_plan, 'member_status': member_status,
    })


# ── 4. Attendance Reports ──────────────────────────────────
@role_required(*ADMIN_ROLES)
def attendance_reports(request):
    date_from, date_to, today = _date_range(request)
    records = AttendanceRecord.objects.filter(date__gte=date_from, date__lte=date_to)

    stats = {
        'total':      records.count(),
        'unique_members': records.values('member').distinct().count(),
        'avg_per_day': 0,
    }
    days_count = (date.fromisoformat(date_to) - date.fromisoformat(date_from)).days + 1
    stats['avg_per_day'] = round(stats['total'] / max(days_count, 1), 1)

    by_status = records.values('status').annotate(count=Count('id')).order_by('-count')
    daily = records.values('date').annotate(count=Count('id')).order_by('date')

    return render(request, 'reports/attendance_reports.html', {
        'stats': stats, 'by_status': by_status, 'daily': daily,
        'date_from': date_from, 'date_to': date_to,
    })


# ── 5. Payment Reports ─────────────────────────────────────
@role_required(*ADMIN_ROLES)
def payment_reports(request):
    date_from, date_to, today = _date_range(request)
    payments = Payment.objects.filter(payment_date__gte=date_from, payment_date__lte=date_to)

    stats = {
        'completed':  payments.filter(status='completed').aggregate(t=Sum('net_amount'))['t'] or 0,
        'pending':    payments.filter(status='pending').count(),
        'failed':     payments.filter(status='failed').count(),
        'refunded':   payments.filter(status='refunded').count(),
    }
    invoices = Invoice.objects.filter(issue_date__gte=date_from, issue_date__lte=date_to)
    invoice_stats = {
        'total':     invoices.count(),
        'paid':      invoices.filter(status='paid').count(),
        'overdue':   invoices.filter(status='overdue').count(),
    }
    return render(request, 'reports/payment_reports.html', {
        'stats': stats, 'invoice_stats': invoice_stats,
        'date_from': date_from, 'date_to': date_to,
    })


# ── 6. Coach Reports ────────────────────────────────────────
@role_required(*ADMIN_ROLES)
def coach_reports(request):
    coaches = Coach.objects.filter(status='active').order_by('-rating')
    stats = {
        'total':       coaches.count(),
        'avg_rating':  coaches.aggregate(a=Avg('rating'))['a'] or 0,
        'total_salary':coaches.aggregate(t=Sum('base_salary'))['t'] or 0,
    }
    top_coaches = coaches[:10]
    return render(request, 'reports/coach_reports.html', {
        'stats': stats, 'top_coaches': top_coaches,
    })


# ── 7. Employee Reports ─────────────────────────────────────
@role_required(*ADMIN_ROLES)
def employee_reports(request):
    employees = Employee.objects.filter(status='active').select_related('department')
    stats = {
        'total':        employees.count(),
        'total_payroll':employees.aggregate(t=Sum('base_salary'))['t'] or 0,
        'avg_salary':   employees.aggregate(a=Avg('base_salary'))['a'] or 0,
    }
    by_department = employees.values('department__name').annotate(count=Count('id'), total_salary=Sum('base_salary')).order_by('-count')
    return render(request, 'reports/employee_reports.html', {
        'stats': stats, 'by_department': by_department,
    })


# ── 8. Inventory Reports ────────────────────────────────────
@role_required(*ADMIN_ROLES)
def inventory_reports(request):
    products = Product.objects.filter(is_active=True).select_related('category')
    total_value = sum(float(p.cost_price) * p.total_stock for p in products)
    stats = {
        'total_products': products.count(),
        'low_stock':      sum(1 for p in products if p.is_low_stock),
        'total_value':    total_value,
    }
    by_category = products.values('category__name').annotate(count=Count('id')).order_by('-count')
    return render(request, 'reports/inventory_reports.html', {
        'stats': stats, 'by_category': by_category,
    })


# ── 9. Sales Reports (POS) ──────────────────────────────────
@role_required(*ADMIN_ROLES)
def sales_reports(request):
    date_from, date_to, today = _date_range(request)
    sales = Sale.objects.filter(status='completed', created_at__date__gte=date_from, created_at__date__lte=date_to)

    stats = {
        'total_sales': sales.count(),
        'revenue':     sales.aggregate(t=Sum('total'))['t'] or 0,
    }
    by_method = sales.values('payment_method').annotate(total=Sum('total'), count=Count('id')).order_by('-total')

    return render(request, 'reports/sales_reports.html', {
        'stats': stats, 'by_method': by_method,
        'date_from': date_from, 'date_to': date_to,
    })


# ── 10. Profit & Loss ───────────────────────────────────────
@role_required(*ADMIN_ROLES)
def profit_loss(request):
    date_from, date_to, today = _date_range(request)

    membership_rev = Payment.objects.filter(status='completed', payment_date__gte=date_from, payment_date__lte=date_to).aggregate(t=Sum('net_amount'))['t'] or 0
    pos_rev = Sale.objects.filter(status='completed', created_at__date__gte=date_from, created_at__date__lte=date_to).aggregate(t=Sum('total'))['t'] or 0
    total_revenue = float(membership_rev) + float(pos_rev)

    payroll_cost = Payroll.objects.filter(month__gte=date_from, month__lte=date_to).aggregate(t=Sum('net_salary'))['t'] or 0
    coach_salary = Coach.objects.filter(status='active').aggregate(t=Sum('base_salary'))['t'] or 0

    total_expenses = float(payroll_cost) + float(coach_salary)
    net_profit = total_revenue - total_expenses

    return render(request, 'reports/profit_loss.html', {
        'membership_rev': membership_rev, 'pos_rev': pos_rev, 'total_revenue': total_revenue,
        'payroll_cost': payroll_cost, 'coach_salary': coach_salary, 'total_expenses': total_expenses,
        'net_profit': net_profit, 'date_from': date_from, 'date_to': date_to,
    })


# ── 11. KPI Dashboard ───────────────────────────────────────
@role_required(*ADMIN_ROLES)
def kpi_dashboard(request):
    today = date.today()
    month_ago = today - timedelta(days=30)
    prev_month_start = month_ago - timedelta(days=30)

    revenue_this = Payment.objects.filter(status='completed', payment_date__gte=month_ago).aggregate(t=Sum('net_amount'))['t'] or 0
    revenue_prev = Payment.objects.filter(status='completed', payment_date__gte=prev_month_start, payment_date__lt=month_ago).aggregate(t=Sum('net_amount'))['t'] or 0
    revenue_growth = round((float(revenue_this) - float(revenue_prev)) / max(float(revenue_prev), 1) * 100, 1)

    new_members_this = Member.objects.filter(created_at__gte=month_ago).count()
    active_members = Member.objects.filter(status='active').count()
    churn_members = Member.objects.filter(status__in=['cancelled','archived'], updated_at__gte=month_ago).count() if hasattr(Member, 'updated_at') else 0

    attendance_rate = AttendanceRecord.objects.filter(date__gte=month_ago).values('member').distinct().count()

    kpis = [
        {'label': 'Revenue Growth', 'value': f'{revenue_growth}%', 'icon': 'fa-chart-line', 'color': 'green' if revenue_growth >= 0 else 'red'},
        {'label': 'New Members (30d)', 'value': new_members_this, 'icon': 'fa-user-plus', 'color': 'blue'},
        {'label': 'Active Members', 'value': active_members, 'icon': 'fa-users', 'color': 'purple'},
        {'label': 'Active Visitors (30d)', 'value': attendance_rate, 'icon': 'fa-calendar-check', 'color': 'orange'},
    ]
    return render(request, 'reports/kpi_dashboard.html', {'kpis': kpis, 'today': today})


# ── 12. Custom Reports ───────────────────────────────────────
@role_required(*ADMIN_ROLES)
def custom_reports(request):
    reports = SavedReport.objects.select_related('created_by').order_by('-created_at')
    return render(request, 'reports/custom_reports.html', {'reports': reports})


@role_required(*ADMIN_ROLES)
def custom_report_new(request):
    if request.method == 'POST':
        SavedReport.objects.create(
            name=request.POST.get('name'), report_type=request.POST.get('report_type', 'custom'),
            date_from=request.POST.get('date_from') or None, date_to=request.POST.get('date_to') or None,
            created_by=request.user,
        )
        messages.success(request, 'Custom report saved!')
        return redirect('reports:custom')
    return render(request, 'reports/custom_report_form.html', {
        'report_types': SavedReport.ReportType.choices,
    })


# ── 13. Export Center ─────────────────────────────────────────
@role_required(*ADMIN_ROLES)
def export_center(request):
    exports = ExportLog.objects.select_related('requested_by').order_by('-created_at')
    return render(request, 'reports/export_center.html', {'exports': exports})


@role_required(*ADMIN_ROLES)
def export_new(request):
    if request.method == 'POST':
        ExportLog.objects.create(
            report_name=request.POST.get('report_name'), format=request.POST.get('format', 'pdf'),
            status='completed', requested_by=request.user,
        )
        messages.success(request, 'Export generated!')
        return redirect('reports:export')
    return render(request, 'reports/export_form.html', {'formats': ExportLog.Format.choices})
