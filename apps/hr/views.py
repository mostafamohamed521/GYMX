from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone

from .models import (
    Employee, Department, Position, Role, Permission,
    Shift, ShiftAssignment, EmployeeAttendance,
    Payroll, Bonus, Deduction, LeaveRequest,
    PerformanceReview, Contract,
)


# ── 1. Employees List ──────────────────────────────────────
@login_required
def employees_list(request):
    employees = Employee.objects.select_related('department','position','role').order_by('first_name')
    q        = request.GET.get('q','')
    status_f = request.GET.get('status','')
    dept_f   = request.GET.get('department','')
    if q:      employees = employees.filter(Q(first_name__icontains=q)|Q(last_name__icontains=q)|Q(email__icontains=q))
    if status_f: employees = employees.filter(status=status_f)
    if dept_f:   employees = employees.filter(department__pk=dept_f)

    stats = {
        'total':   Employee.objects.count(),
        'active':  Employee.objects.filter(status='active').count(),
        'on_leave':Employee.objects.filter(status='on_leave').count(),
        'depts':   Department.objects.count(),
    }
    depts = Department.objects.all()
    return render(request, 'hr/employees_list.html', {
        'employees': employees, 'stats': stats, 'depts': depts,
        'q': q, 'status_f': status_f, 'dept_f': dept_f,
        'statuses': Employee.Status.choices,
    })


# ── 2. Add Employee ────────────────────────────────────────
@login_required
def employee_add(request):
    if request.method == 'POST':
        try:
            dept_pk = request.POST.get('department')
            pos_pk  = request.POST.get('position')
            role_pk = request.POST.get('role')
            emp = Employee.objects.create(
                first_name  = request.POST.get('first_name'),
                last_name   = request.POST.get('last_name'),
                email       = request.POST.get('email'),
                phone       = request.POST.get('phone'),
                gender      = request.POST.get('gender','male'),
                birth_date  = request.POST.get('birth_date') or None,
                address     = request.POST.get('address',''),
                national_id = request.POST.get('national_id',''),
                department  = Department.objects.filter(pk=dept_pk).first() if dept_pk else None,
                position    = Position.objects.filter(pk=pos_pk).first() if pos_pk else None,
                role        = Role.objects.filter(pk=role_pk).first() if role_pk else None,
                employment_type = request.POST.get('employment_type','full_time'),
                hire_date   = request.POST.get('hire_date') or date.today(),
                base_salary = float(request.POST.get('base_salary',0)),
                emergency_contact_name  = request.POST.get('emergency_contact_name',''),
                emergency_contact_phone = request.POST.get('emergency_contact_phone',''),
            )
            if 'profile_image' in request.FILES:
                emp.profile_image = request.FILES['profile_image']
                emp.save(update_fields=['profile_image'])
            messages.success(request, f'Employee {emp.get_full_name()} added!')
            return redirect('hr:detail', pk=emp.pk)
        except Exception as e:
            messages.error(request, f'Error: {e}')

    return render(request, 'hr/employee_form.html', {
        'depts': Department.objects.all(),
        'positions': Position.objects.all(),
        'roles': Role.objects.all(),
        'statuses': Employee.Status.choices,
        'employment_types': Employee.EmploymentType.choices,
        'today': date.today(), 'action': 'Add', 'page_title': 'Add Employee',
    })


# ── 3. Employee Detail ─────────────────────────────────────
@login_required
def employee_detail(request, pk):
    emp = get_object_or_404(Employee.objects.select_related('department','position','role'), pk=pk)
    today = date.today()
    month_ago = today - timedelta(days=30)

    stats = {
        'attendance_month': EmployeeAttendance.objects.filter(employee=emp, date__gte=month_ago, status='present').count(),
        'leave_pending':    LeaveRequest.objects.filter(employee=emp, status='pending').count(),
        'last_payroll':     Payroll.objects.filter(employee=emp).first(),
        'active_contract':  Contract.objects.filter(employee=emp, status='active').first(),
    }
    reviews = emp.performance_reviews.all()[:3]
    return render(request, 'hr/employee_detail.html', {
        'emp': emp, 'stats': stats, 'reviews': reviews, 'today': today,
    })


# ── 4. Departments ─────────────────────────────────────────
@login_required
def departments(request):
    if request.method == 'POST':
        Department.objects.create(
            name=request.POST.get('name'),
            description=request.POST.get('description',''),
        )
        messages.success(request, 'Department added.')
        return redirect('hr:departments')

    depts = Department.objects.annotate(emp_count=Count('employees')).order_by('name')
    return render(request, 'hr/departments.html', {'depts': depts})


# ── 5. Positions ───────────────────────────────────────────
@login_required
def positions(request):
    if request.method == 'POST':
        dept_pk = request.POST.get('department')
        Position.objects.create(
            title=request.POST.get('title'),
            department=Department.objects.filter(pk=dept_pk).first() if dept_pk else None,
            description=request.POST.get('description',''),
            min_salary=float(request.POST.get('min_salary',0)),
            max_salary=float(request.POST.get('max_salary',0)),
        )
        messages.success(request, 'Position added.')
        return redirect('hr:positions')

    pos = Position.objects.select_related('department').annotate(emp_count=Count('employees')).order_by('title')
    depts = Department.objects.all()
    return render(request, 'hr/positions.html', {'pos': pos, 'depts': depts})


# ── 6. Roles ───────────────────────────────────────────────
@login_required
def roles(request):
    if request.method == 'POST':
        Role.objects.create(name=request.POST.get('name'), description=request.POST.get('description',''))
        messages.success(request, 'Role added.')
        return redirect('hr:roles')

    role_list = Role.objects.annotate(emp_count=Count('employees')).order_by('name')
    return render(request, 'hr/roles.html', {'roles': role_list})


# ── 7. Permissions ─────────────────────────────────────────
@login_required
def permissions(request):
    role_list = Role.objects.all()
    return render(request, 'hr/permissions.html', {'roles': role_list})


@login_required
def permissions_edit(request, role_pk):
    role = get_object_or_404(Role, pk=role_pk)
    MODULES = ['Members','Payments','Coaches','Workouts','Nutrition','Classes','HR','Inventory','POS']

    if request.method == 'POST':
        for module in MODULES:
            Permission.objects.update_or_create(
                role=role, module=module,
                defaults={
                    'can_view':   bool(request.POST.get(f'view_{module}')),
                    'can_add':    bool(request.POST.get(f'add_{module}')),
                    'can_edit':   bool(request.POST.get(f'edit_{module}')),
                    'can_delete': bool(request.POST.get(f'delete_{module}')),
                }
            )
        messages.success(request, f'Permissions updated for {role.name}.')
        return redirect('hr:permissions')

    existing = {p.module: p for p in role.permissions.all()}
    return render(request, 'hr/permissions_edit.html', {
        'role': role, 'modules': MODULES, 'existing': existing,
    })


# ── 8. Shift Management ────────────────────────────────────
@login_required
def shift_management(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_shift':
            Shift.objects.create(
                name=request.POST.get('name'),
                start_time=request.POST.get('start_time'),
                end_time=request.POST.get('end_time'),
                description=request.POST.get('description',''),
            )
            messages.success(request, 'Shift created.')
        elif action == 'assign':
            emp   = get_object_or_404(Employee, pk=request.POST.get('employee'))
            shift = get_object_or_404(Shift, pk=request.POST.get('shift'))
            day   = int(request.POST.get('day_of_week'))
            ShiftAssignment.objects.update_or_create(
                employee=emp, day_of_week=day, defaults={'shift': shift}
            )
            messages.success(request, f'{emp.get_full_name()} assigned to {shift.name}.')
        return redirect('hr:shifts')

    shifts     = Shift.objects.all()
    employees  = Employee.objects.filter(status='active').order_by('first_name')
    assignments= ShiftAssignment.objects.select_related('employee','shift').order_by('day_of_week')
    days       = ShiftAssignment.DAYS

    grid = {i: [] for i in range(7)}
    for a in assignments:
        grid[a.day_of_week].append(a)

    return render(request, 'hr/shift_management.html', {
        'shifts': shifts, 'employees': employees, 'grid': grid, 'days': days,
    })


# ── 9. Employee Attendance ─────────────────────────────────
@login_required
def employee_attendance(request):
    today = date.today()
    if request.method == 'POST':
        emp    = get_object_or_404(Employee, pk=request.POST.get('employee'))
        d      = request.POST.get('date', str(today))
        EmployeeAttendance.objects.update_or_create(
            employee=emp, date=d,
            defaults={
                'status': request.POST.get('status','present'),
                'check_in': request.POST.get('check_in') or None,
                'check_out': request.POST.get('check_out') or None,
                'notes': request.POST.get('notes',''),
            }
        )
        messages.success(request, f'Attendance recorded for {emp.get_full_name()}.')
        return redirect('hr:attendance')

    records   = EmployeeAttendance.objects.select_related('employee').filter(date=today)
    employees = Employee.objects.filter(status='active').order_by('first_name')

    stats = {
        'present': records.filter(status='present').count(),
        'absent':  records.filter(status='absent').count(),
        'late':    records.filter(status='late').count(),
        'leave':   records.filter(status='leave').count(),
    }
    return render(request, 'hr/employee_attendance.html', {
        'records': records, 'employees': employees, 'stats': stats,
        'today': today, 'statuses': EmployeeAttendance.Status.choices,
    })


# ── 10. Payroll ────────────────────────────────────────────
@login_required
def payroll(request):
    today = date.today()
    if request.method == 'POST':
        emp   = get_object_or_404(Employee, pk=request.POST.get('employee'))
        month = date.fromisoformat(request.POST.get('month') + '-01')
        bonuses    = Bonus.objects.filter(employee=emp, date__year=month.year, date__month=month.month).aggregate(t=Sum('amount'))['t'] or 0
        deductions = Deduction.objects.filter(employee=emp, date__year=month.year, date__month=month.month).aggregate(t=Sum('amount'))['t'] or 0

        Payroll.objects.update_or_create(
            employee=emp, month=month,
            defaults={
                'base_salary': float(request.POST.get('base_salary', emp.base_salary)),
                'bonuses': float(bonuses), 'deductions': float(deductions),
                'status': request.POST.get('status','pending'),
                'paid_date': request.POST.get('paid_date') or None,
            }
        )
        messages.success(request, f'Payroll processed for {emp.get_full_name()}.')
        return redirect('hr:payroll')

    payrolls = Payroll.objects.select_related('employee').order_by('-month')[:100]
    employees= Employee.objects.filter(status='active').order_by('first_name')
    stats = {
        'total_paid':   Payroll.objects.filter(status='paid').aggregate(t=Sum('net_salary'))['t'] or 0,
        'pending':      Payroll.objects.filter(status='pending').count(),
        'this_month':   Payroll.objects.filter(month__year=today.year, month__month=today.month).count(),
    }
    return render(request, 'hr/payroll.html', {
        'payrolls': payrolls, 'employees': employees, 'stats': stats,
        'statuses': Payroll.Status.choices, 'current_month': today.strftime('%Y-%m'),
    })


# ── 11. Salaries ───────────────────────────────────────────
@login_required
def salaries(request):
    employees = Employee.objects.filter(status='active').select_related('department','position').order_by('-base_salary')
    stats = {
        'total_payroll': employees.aggregate(t=Sum('base_salary'))['t'] or 0,
        'avg_salary':    employees.aggregate(a=Avg('base_salary'))['a'] or 0,
        'highest':       employees.order_by('-base_salary').first(),
    }
    return render(request, 'hr/salaries.html', {'employees': employees, 'stats': stats})


# ── 12. Bonuses ────────────────────────────────────────────
@login_required
def bonuses(request):
    if request.method == 'POST':
        emp = get_object_or_404(Employee, pk=request.POST.get('employee'))
        Bonus.objects.create(
            employee=emp, title=request.POST.get('title'),
            amount=float(request.POST.get('amount',0)),
            date=request.POST.get('date') or date.today(),
            reason=request.POST.get('reason',''),
        )
        messages.success(request, f'Bonus added for {emp.get_full_name()}.')
        return redirect('hr:bonuses')

    bonus_list = Bonus.objects.select_related('employee').order_by('-date')
    employees  = Employee.objects.filter(status='active').order_by('first_name')
    total = bonus_list.aggregate(t=Sum('amount'))['t'] or 0
    return render(request, 'hr/bonuses.html', {
        'bonus_list': bonus_list, 'employees': employees, 'total': total, 'today': date.today(),
    })


# ── 13. Deductions ─────────────────────────────────────────
@login_required
def deductions(request):
    if request.method == 'POST':
        emp = get_object_or_404(Employee, pk=request.POST.get('employee'))
        Deduction.objects.create(
            employee=emp, title=request.POST.get('title'),
            amount=float(request.POST.get('amount',0)),
            reason=request.POST.get('reason','other'),
            date=request.POST.get('date') or date.today(),
            notes=request.POST.get('notes',''),
        )
        messages.success(request, f'Deduction added for {emp.get_full_name()}.')
        return redirect('hr:deductions')

    deduction_list = Deduction.objects.select_related('employee').order_by('-date')
    employees      = Employee.objects.filter(status='active').order_by('first_name')
    total = deduction_list.aggregate(t=Sum('amount'))['t'] or 0
    return render(request, 'hr/deductions.html', {
        'deduction_list': deduction_list, 'employees': employees, 'total': total,
        'reasons': Deduction.Reason.choices, 'today': date.today(),
    })


# ── 14. Leave Requests ──────────────────────────────────────
@login_required
def leave_requests(request):
    if request.method == 'POST':
        emp = get_object_or_404(Employee, pk=request.POST.get('employee'))
        LeaveRequest.objects.create(
            employee=emp, leave_type=request.POST.get('leave_type','annual'),
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'),
            reason=request.POST.get('reason',''),
        )
        messages.success(request, f'Leave request submitted for {emp.get_full_name()}.')
        return redirect('hr:leave')

    requests_qs = LeaveRequest.objects.select_related('employee').order_by('-requested_at')
    status_f = request.GET.get('status','')
    if status_f: requests_qs = requests_qs.filter(status=status_f)

    employees = Employee.objects.filter(status='active').order_by('first_name')
    stats = {
        'pending':  LeaveRequest.objects.filter(status='pending').count(),
        'approved': LeaveRequest.objects.filter(status='approved').count(),
        'total':    LeaveRequest.objects.count(),
    }
    return render(request, 'hr/leave_requests.html', {
        'requests': requests_qs, 'employees': employees, 'stats': stats,
        'status_f': status_f, 'statuses': LeaveRequest.Status.choices,
        'leave_types': LeaveRequest.LeaveType.choices, 'today': date.today(),
    })


@login_required
def leave_action(request, pk):
    lr = get_object_or_404(LeaveRequest, pk=pk)
    action = request.POST.get('action')
    if action == 'approve':
        lr.status = 'approved'
        lr.approved_by = request.user
        lr.reviewed_at = timezone.now()
        lr.save()
        messages.success(request, 'Leave approved.')
    elif action == 'reject':
        lr.status = 'rejected'
        lr.approved_by = request.user
        lr.reviewed_at = timezone.now()
        lr.save()
        messages.info(request, 'Leave rejected.')
    return redirect('hr:leave')


# ── 15. Performance Reviews ─────────────────────────────────
@login_required
def performance_reviews(request):
    reviews = PerformanceReview.objects.select_related('employee').order_by('-review_date')
    stats = {
        'total':    PerformanceReview.objects.count(),
        'avg_rating': PerformanceReview.objects.aggregate(a=Avg('rating'))['a'] or 0,
    }
    return render(request, 'hr/performance_reviews.html', {'reviews': reviews, 'stats': stats})


@login_required
def performance_new(request):
    if request.method == 'POST':
        emp = get_object_or_404(Employee, pk=request.POST.get('employee'))
        PerformanceReview.objects.create(
            employee=emp, review_period=request.POST.get('review_period'),
            reviewed_by=request.user, rating=int(request.POST.get('rating',3)),
            strengths=request.POST.get('strengths',''),
            improvements=request.POST.get('improvements',''),
            goals=request.POST.get('goals',''),
            comments=request.POST.get('comments',''),
            review_date=request.POST.get('review_date') or date.today(),
        )
        messages.success(request, f'Performance review added for {emp.get_full_name()}.')
        return redirect('hr:performance')

    employees = Employee.objects.filter(status='active').order_by('first_name')
    return render(request, 'hr/performance_form.html', {
        'employees': employees, 'ratings': PerformanceReview.Rating.choices, 'today': date.today(),
    })


# ── 16. Contracts ──────────────────────────────────────────
@login_required
def contracts(request):
    contract_list = Contract.objects.select_related('employee').order_by('-start_date')
    stats = {
        'total':      Contract.objects.count(),
        'active':     Contract.objects.filter(status='active').count(),
        'expiring':   sum(1 for c in Contract.objects.filter(status='active') if c.is_expiring_soon),
    }
    return render(request, 'hr/contracts.html', {'contract_list': contract_list, 'stats': stats})


@login_required
def contract_new(request):
    if request.method == 'POST':
        emp = get_object_or_404(Employee, pk=request.POST.get('employee'))
        c = Contract(
            employee=emp, contract_type=request.POST.get('contract_type'),
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date') or None,
            salary=float(request.POST.get('salary',0)),
            status=request.POST.get('status','active'),
            notes=request.POST.get('notes',''),
        )
        if 'document' in request.FILES:
            c.document = request.FILES['document']
        c.save()
        messages.success(request, f'Contract created for {emp.get_full_name()}.')
        return redirect('hr:contracts')

    employees = Employee.objects.filter(status='active').order_by('first_name')
    return render(request, 'hr/contract_form.html', {
        'employees': employees, 'statuses': Contract.Status.choices, 'today': date.today(),
    })
