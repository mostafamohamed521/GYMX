from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone

from apps.accounts.permissions import role_required, ADMIN_ROLES
from .models import Branch, BranchSettings, MemberTransfer, EmployeeTransfer
from apps.members.models import Member
from apps.hr.models import Employee
from apps.payments.models import Payment
from apps.accounts.models import User


# ── 1. Branches List ───────────────────────────────────────
@role_required(*ADMIN_ROLES)
def branches_list(request):
    branches = Branch.objects.all()
    stats = {
        'total':    Branch.objects.count(),
        'active':   Branch.objects.filter(status='active').count(),
        'members':  Member.objects.filter(branch__isnull=False).count(),
        'employees':Employee.objects.filter(branch__isnull=False).count(),
    }
    return render(request, 'branches/branches_list.html', {
        'branches': branches, 'stats': stats,
    })


# ── 2. Add Branch ──────────────────────────────────────────
@role_required(*ADMIN_ROLES)
def branch_add(request):
    if request.method == 'POST':
        try:
            manager_pk = request.POST.get('manager')
            branch = Branch(
                name         = request.POST.get('name'),
                address      = request.POST.get('address',''),
                city         = request.POST.get('city',''),
                phone        = request.POST.get('phone',''),
                email        = request.POST.get('email',''),
                manager      = User.objects.filter(pk=manager_pk).first() if manager_pk else None,
                status       = request.POST.get('status','active'),
                opening_time = request.POST.get('opening_time','06:00'),
                closing_time = request.POST.get('closing_time','23:00'),
                max_capacity = int(request.POST.get('max_capacity',200)),
                is_main_branch = bool(request.POST.get('is_main_branch')),
                notes        = request.POST.get('notes',''),
            )
            if 'image' in request.FILES:
                branch.image = request.FILES['image']
            branch.save()
            BranchSettings.objects.get_or_create(branch=branch)
            messages.success(request, f'Branch "{branch.name}" created!')
            return redirect('branches:detail', pk=branch.pk)
        except Exception as e:
            messages.error(request, f'Error: {e}')

    managers = User.objects.filter(role__in=['super_admin','gym_manager'])
    return render(request, 'branches/branch_form.html', {
        'managers': managers, 'statuses': Branch.Status.choices,
        'action': 'Add', 'page_title': 'Add Branch',
    })


# ── 3. Branch Details ──────────────────────────────────────
@role_required(*ADMIN_ROLES)
def branch_detail(request, pk):
    branch = get_object_or_404(Branch, pk=pk)

    if request.method == 'POST':
        try:
            manager_pk = request.POST.get('manager')
            branch.name         = request.POST.get('name', branch.name)
            branch.address      = request.POST.get('address','')
            branch.city         = request.POST.get('city','')
            branch.phone        = request.POST.get('phone','')
            branch.email        = request.POST.get('email','')
            branch.manager      = User.objects.filter(pk=manager_pk).first() if manager_pk else None
            branch.status       = request.POST.get('status', branch.status)
            branch.opening_time = request.POST.get('opening_time', branch.opening_time)
            branch.closing_time = request.POST.get('closing_time', branch.closing_time)
            branch.max_capacity = int(request.POST.get('max_capacity', branch.max_capacity))
            branch.is_main_branch = bool(request.POST.get('is_main_branch'))
            branch.notes        = request.POST.get('notes','')
            if 'image' in request.FILES:
                branch.image = request.FILES['image']
            branch.save()
            messages.success(request, 'Branch updated!')
            return redirect('branches:detail', pk=pk)
        except Exception as e:
            messages.error(request, f'Error: {e}')

    managers = User.objects.filter(role__in=['super_admin','gym_manager'])
    return render(request, 'branches/branch_detail.html', {
        'branch': branch, 'managers': managers, 'statuses': Branch.Status.choices,
    })


# ── 4. Branch Dashboard ────────────────────────────────────
@role_required(*ADMIN_ROLES)
def branch_dashboard(request, pk):
    branch = get_object_or_404(Branch, pk=pk)
    today  = date.today()
    month_ago = today - timedelta(days=30)

    members   = Member.objects.filter(branch=branch)
    employees = Employee.objects.filter(branch=branch)
    revenue   = Payment.objects.filter(member__branch=branch, status='completed', payment_date__gte=month_ago).aggregate(t=Sum('net_amount'))['t'] or 0

    stats = {
        'total_members':   members.count(),
        'active_members':  members.filter(status='active').count(),
        'total_employees': employees.filter(status='active').count(),
        'revenue_30d':     revenue,
        'capacity_pct':    min(int(members.count() / max(branch.max_capacity,1) * 100), 100),
    }
    monthly = []
    for i in range(5,-1,-1):
        d = today.replace(day=1) - timedelta(days=i*30)
        rev = Payment.objects.filter(member__branch=branch, status='completed', payment_date__year=d.year, payment_date__month=d.month).aggregate(t=Sum('net_amount'))['t'] or 0
        monthly.append({'label': d.strftime('%b'), 'revenue': float(rev)})

    return render(request, 'branches/branch_dashboard.html', {
        'branch': branch, 'stats': stats, 'monthly': monthly,
    })


# ── 5. Branch Employees ────────────────────────────────────
@role_required(*ADMIN_ROLES)
def branch_employees(request, pk):
    branch    = get_object_or_404(Branch, pk=pk)
    employees = Employee.objects.filter(branch=branch).select_related('department','position')
    return render(request, 'branches/branch_employees.html', {
        'branch': branch, 'employees': employees,
    })


# ── 6. Branch Members ───────────────────────────────────────
@role_required(*ADMIN_ROLES)
def branch_members(request, pk):
    branch  = get_object_or_404(Branch, pk=pk)
    members = Member.objects.filter(branch=branch)
    return render(request, 'branches/branch_members.html', {
        'branch': branch, 'members': members,
    })


# ── 7. Branch Revenue ───────────────────────────────────────
@role_required(*ADMIN_ROLES)
def branch_revenue(request, pk):
    branch = get_object_or_404(Branch, pk=pk)
    today  = date.today()
    date_from = request.GET.get('from', str(today.replace(day=1)))
    date_to   = request.GET.get('to', str(today))

    payments = Payment.objects.filter(
        member__branch=branch, status='completed',
        payment_date__gte=date_from, payment_date__lte=date_to,
    )
    stats = {
        'total_revenue': payments.aggregate(t=Sum('net_amount'))['t'] or 0,
        'total_count':   payments.count(),
    }
    type_breakdown = payments.values('payment_type').annotate(total=Sum('net_amount'), count=Count('id')).order_by('-total')

    return render(request, 'branches/branch_revenue.html', {
        'branch': branch, 'stats': stats, 'type_breakdown': type_breakdown,
        'date_from': date_from, 'date_to': date_to,
    })


# ── 8. Branch Settings ──────────────────────────────────────
@role_required(*ADMIN_ROLES)
def branch_settings(request, pk):
    branch = get_object_or_404(Branch, pk=pk)
    settings_obj, _ = BranchSettings.objects.get_or_create(branch=branch)

    if request.method == 'POST':
        settings_obj.allow_walk_ins        = bool(request.POST.get('allow_walk_ins'))
        settings_obj.allow_online_booking  = bool(request.POST.get('allow_online_booking'))
        settings_obj.require_appointment   = bool(request.POST.get('require_appointment'))
        settings_obj.tax_rate              = float(request.POST.get('tax_rate', 0))
        settings_obj.currency              = request.POST.get('currency','EGP')
        settings_obj.save()
        messages.success(request, 'Branch settings updated!')
        return redirect('branches:settings', pk=pk)

    return render(request, 'branches/branch_settings.html', {
        'branch': branch, 'settings_obj': settings_obj,
    })


# ── 9. Transfer Members ────────────────────────────────────
@role_required(*ADMIN_ROLES)
def transfer_members(request):
    if request.method == 'POST':
        member = get_object_or_404(Member, pk=request.POST.get('member'))
        to_branch = get_object_or_404(Branch, pk=request.POST.get('to_branch'))
        MemberTransfer.objects.create(
            member=member, from_branch=member.branch, to_branch=to_branch,
            reason=request.POST.get('reason',''), requested_by=request.user,
        )
        messages.success(request, f'Transfer request created for {member.get_full_name()}.')
        return redirect('branches:transfer_members')

    transfers = MemberTransfer.objects.select_related('member','from_branch','to_branch').order_by('-requested_at')
    members   = Member.objects.filter(status='active').select_related('branch').order_by('first_name')
    branches  = Branch.objects.filter(status='active')

    return render(request, 'branches/transfer_members.html', {
        'transfers': transfers, 'members': members, 'branches': branches,
    })


@role_required(*ADMIN_ROLES)
def member_transfer_action(request, pk):
    transfer = get_object_or_404(MemberTransfer, pk=pk)
    action = request.POST.get('action')
    if action == 'approve':
        transfer.status = 'approved'
        transfer.processed_at = timezone.now()
        transfer.save()
        transfer.member.branch = transfer.to_branch
        transfer.member.save(update_fields=['branch'])
        messages.success(request, 'Transfer approved and member moved.')
    elif action == 'reject':
        transfer.status = 'rejected'
        transfer.processed_at = timezone.now()
        transfer.save()
        messages.info(request, 'Transfer rejected.')
    return redirect('branches:transfer_members')


# ── 10. Transfer Employees ─────────────────────────────────
@role_required(*ADMIN_ROLES)
def transfer_employees(request):
    if request.method == 'POST':
        employee = get_object_or_404(Employee, pk=request.POST.get('employee'))
        to_branch = get_object_or_404(Branch, pk=request.POST.get('to_branch'))
        EmployeeTransfer.objects.create(
            employee=employee, from_branch=employee.branch, to_branch=to_branch,
            reason=request.POST.get('reason',''), requested_by=request.user,
        )
        messages.success(request, f'Transfer request created for {employee.get_full_name()}.')
        return redirect('branches:transfer_employees')

    transfers = EmployeeTransfer.objects.select_related('employee','from_branch','to_branch').order_by('-requested_at')
    employees = Employee.objects.filter(status='active').select_related('branch').order_by('first_name')
    branches  = Branch.objects.filter(status='active')

    return render(request, 'branches/transfer_employees.html', {
        'transfers': transfers, 'employees': employees, 'branches': branches,
    })


@role_required(*ADMIN_ROLES)
def employee_transfer_action(request, pk):
    transfer = get_object_or_404(EmployeeTransfer, pk=pk)
    action = request.POST.get('action')
    if action == 'approve':
        transfer.status = 'approved'
        transfer.processed_at = timezone.now()
        transfer.save()
        transfer.employee.branch = transfer.to_branch
        transfer.employee.save(update_fields=['branch'])
        messages.success(request, 'Transfer approved and employee moved.')
    elif action == 'reject':
        transfer.status = 'rejected'
        transfer.processed_at = timezone.now()
        transfer.save()
        messages.info(request, 'Transfer rejected.')
    return redirect('branches:transfer_employees')
