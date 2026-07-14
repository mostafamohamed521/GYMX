from django.db import models
from django.utils import timezone
from apps.accounts.models import User


class Department(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    manager     = models.ForeignKey('Employee', on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='managed_departments')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'departments'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def employee_count(self):
        return self.employees.count()


class Position(models.Model):
    title       = models.CharField(max_length=100)
    department  = models.ForeignKey(Department, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='positions')
    description = models.TextField(blank=True)
    min_salary  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_salary  = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = 'positions'
        ordering = ['title']

    def __str__(self):
        return self.title


class Role(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'hr_roles'
        ordering = ['name']

    def __str__(self):
        return self.name


class Permission(models.Model):
    role        = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='permissions')
    module      = models.CharField(max_length=100)
    can_view    = models.BooleanField(default=True)
    can_add     = models.BooleanField(default=False)
    can_edit    = models.BooleanField(default=False)
    can_delete  = models.BooleanField(default=False)

    class Meta:
        db_table = 'hr_permissions'
        unique_together = ['role', 'module']

    def __str__(self):
        return f"{self.role.name} — {self.module}"


class Employee(models.Model):
    class Status(models.TextChoices):
        ACTIVE      = 'active',      'Active'
        ON_LEAVE    = 'on_leave',    'On Leave'
        SUSPENDED   = 'suspended',   'Suspended'
        TERMINATED  = 'terminated', 'Terminated'

    class EmploymentType(models.TextChoices):
        FULL_TIME = 'full_time', 'Full Time'
        PART_TIME = 'part_time', 'Part Time'
        CONTRACT  = 'contract',  'Contract'
        INTERN    = 'intern',    'Intern'

    user            = models.OneToOneField(User, on_delete=models.CASCADE,
                                           null=True, blank=True, related_name='employee_profile')
    employee_id     = models.CharField(max_length=20, unique=True, editable=False)
    first_name      = models.CharField(max_length=100)
    last_name       = models.CharField(max_length=100)
    email           = models.EmailField(unique=True)
    phone           = models.CharField(max_length=20)
    profile_image   = models.ImageField(upload_to='employees/', null=True, blank=True)
    gender          = models.CharField(max_length=10, choices=[('male','Male'),('female','Female')], default='male')
    birth_date      = models.DateField(null=True, blank=True)
    address         = models.TextField(blank=True)
    national_id     = models.CharField(max_length=30, blank=True)

    department      = models.ForeignKey(Department, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='employees')
    branch          = models.ForeignKey('branches.Branch', on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='employees')
    position        = models.ForeignKey(Position, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='employees')
    role            = models.ForeignKey(Role, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='employees')
    employment_type = models.CharField(max_length=12, choices=EmploymentType.choices,
                                       default=EmploymentType.FULL_TIME)
    status          = models.CharField(max_length=12, choices=Status.choices,
                                       default=Status.ACTIVE)
    hire_date       = models.DateField(default=timezone.now)
    base_salary     = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    emergency_contact_name  = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)

    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'employees'
        ordering = ['first_name']

    def __str__(self):
        return self.get_full_name()

    def save(self, *args, **kwargs):
        if not self.employee_id:
            last = Employee.objects.count() + 1
            self.employee_id = f"EMP-{str(last).zfill(4)}"
        super().save(*args, **kwargs)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_initials(self):
        return f"{self.first_name[0]}{self.last_name[0]}".upper()

    def get_status_color(self):
        return {'active':'green','on_leave':'orange','suspended':'red','terminated':'gray'}.get(self.status,'gray')


class Shift(models.Model):
    name        = models.CharField(max_length=100)
    start_time  = models.TimeField()
    end_time    = models.TimeField()
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'shifts'
        ordering = ['start_time']

    def __str__(self):
        return f"{self.name} ({self.start_time}–{self.end_time})"


class ShiftAssignment(models.Model):
    DAYS = [(0,'Monday'),(1,'Tuesday'),(2,'Wednesday'),(3,'Thursday'),(4,'Friday'),(5,'Saturday'),(6,'Sunday')]

    employee    = models.ForeignKey(Employee, on_delete=models.CASCADE,
                                    related_name='shift_assignments')
    shift       = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='assignments')
    day_of_week = models.IntegerField(choices=DAYS)

    class Meta:
        db_table = 'shift_assignments'
        unique_together = ['employee', 'day_of_week']
        ordering = ['day_of_week']

    def __str__(self):
        return f"{self.employee.get_full_name()} — {self.get_day_of_week_display()} — {self.shift.name}"


class EmployeeAttendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = 'present', 'Present'
        ABSENT  = 'absent',  'Absent'
        LATE    = 'late',    'Late'
        LEAVE   = 'leave',   'On Leave'
        HOLIDAY = 'holiday', 'Holiday'

    employee    = models.ForeignKey(Employee, on_delete=models.CASCADE,
                                    related_name='attendance')
    date        = models.DateField()
    status      = models.CharField(max_length=10, choices=Status.choices,
                                   default=Status.PRESENT)
    check_in    = models.TimeField(null=True, blank=True)
    check_out   = models.TimeField(null=True, blank=True)
    notes       = models.TextField(blank=True)

    class Meta:
        db_table = 'employee_attendance'
        unique_together = ['employee', 'date']
        ordering = ['-date']

    def get_status_color(self):
        return {'present':'green','absent':'red','late':'orange','leave':'blue','holiday':'purple'}.get(self.status,'gray')


class Payroll(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID    = 'paid',    'Paid'
        HELD    = 'held',    'Held'

    employee    = models.ForeignKey(Employee, on_delete=models.CASCADE,
                                    related_name='payrolls')
    month       = models.DateField()
    base_salary = models.DecimalField(max_digits=10, decimal_places=2)
    bonuses     = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_salary  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status      = models.CharField(max_length=10, choices=Status.choices,
                                   default=Status.PENDING)
    paid_date   = models.DateField(null=True, blank=True)
    notes       = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payroll'
        unique_together = ['employee', 'month']
        ordering = ['-month']

    def save(self, *args, **kwargs):
        self.net_salary = float(self.base_salary) + float(self.bonuses) - float(self.deductions)
        super().save(*args, **kwargs)

    def get_status_color(self):
        return {'pending':'orange','paid':'green','held':'red'}.get(self.status,'gray')


class Bonus(models.Model):
    employee    = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='bonuses_list')
    title       = models.CharField(max_length=200)
    amount      = models.DecimalField(max_digits=10, decimal_places=2)
    date        = models.DateField(default=timezone.now)
    reason      = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bonuses'
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee.get_full_name()} — {self.title}"


class Deduction(models.Model):
    class Reason(models.TextChoices):
        LATE      = 'late',      'Late Arrival'
        ABSENCE   = 'absence',   'Unexcused Absence'
        DAMAGE    = 'damage',    'Damage/Loss'
        ADVANCE   = 'advance',   'Salary Advance'
        OTHER     = 'other',     'Other'

    employee    = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='deductions_list')
    title       = models.CharField(max_length=200)
    amount      = models.DecimalField(max_digits=10, decimal_places=2)
    reason      = models.CharField(max_length=10, choices=Reason.choices, default=Reason.OTHER)
    date        = models.DateField(default=timezone.now)
    notes       = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'deductions'
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee.get_full_name()} — {self.title}"


class LeaveRequest(models.Model):
    class LeaveType(models.TextChoices):
        ANNUAL   = 'annual',   'Annual Leave'
        SICK     = 'sick',     'Sick Leave'
        UNPAID   = 'unpaid',   'Unpaid Leave'
        EMERGENCY= 'emergency','Emergency Leave'
        MATERNITY= 'maternity','Maternity/Paternity'

    class Status(models.TextChoices):
        PENDING  = 'pending',  'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    employee    = models.ForeignKey(Employee, on_delete=models.CASCADE,
                                    related_name='leave_requests')
    leave_type  = models.CharField(max_length=10, choices=LeaveType.choices,
                                   default=LeaveType.ANNUAL)
    start_date  = models.DateField()
    end_date    = models.DateField()
    reason      = models.TextField(blank=True)
    status      = models.CharField(max_length=10, choices=Status.choices,
                                   default=Status.PENDING)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='approved_leaves')
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'leave_requests'
        ordering = ['-requested_at']

    def __str__(self):
        return f"{self.employee.get_full_name()} — {self.get_leave_type_display()}"

    @property
    def days_count(self):
        return (self.end_date - self.start_date).days + 1

    def get_status_color(self):
        return {'pending':'orange','approved':'green','rejected':'red'}.get(self.status,'gray')


class PerformanceReview(models.Model):
    class Rating(models.IntegerChoices):
        POOR       = 1, 'Poor'
        BELOW_AVG  = 2, 'Below Average'
        AVERAGE    = 3, 'Average'
        GOOD       = 4, 'Good'
        EXCELLENT  = 5, 'Excellent'

    employee     = models.ForeignKey(Employee, on_delete=models.CASCADE,
                                     related_name='performance_reviews')
    review_period= models.CharField(max_length=100, help_text='e.g. Q1 2026')
    reviewed_by  = models.ForeignKey(User, on_delete=models.SET_NULL,
                                     null=True, blank=True)
    rating       = models.IntegerField(choices=Rating.choices, default=Rating.AVERAGE)
    strengths    = models.TextField(blank=True)
    improvements = models.TextField(blank=True)
    goals        = models.TextField(blank=True)
    comments     = models.TextField(blank=True)
    review_date  = models.DateField(default=timezone.now)

    class Meta:
        db_table = 'performance_reviews'
        ordering = ['-review_date']

    def __str__(self):
        return f"{self.employee.get_full_name()} — {self.review_period}"

    def get_rating_color(self):
        return {1:'red',2:'orange',3:'gray',4:'blue',5:'green'}.get(self.rating,'gray')


class Contract(models.Model):
    class Status(models.TextChoices):
        ACTIVE   = 'active',   'Active'
        EXPIRED  = 'expired',  'Expired'
        RENEWED  = 'renewed',  'Renewed'
        TERMINATED = 'terminated', 'Terminated'

    employee    = models.ForeignKey(Employee, on_delete=models.CASCADE,
                                    related_name='contracts')
    contract_type = models.CharField(max_length=100, default='Employment Contract')
    start_date  = models.DateField()
    end_date    = models.DateField(null=True, blank=True)
    salary      = models.DecimalField(max_digits=10, decimal_places=2)
    status      = models.CharField(max_length=12, choices=Status.choices,
                                   default=Status.ACTIVE)
    document    = models.FileField(upload_to='contracts/', null=True, blank=True)
    notes       = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'contracts'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.employee.get_full_name()} — {self.contract_type}"

    def get_status_color(self):
        return {'active':'green','expired':'red','renewed':'blue','terminated':'gray'}.get(self.status,'gray')

    @property
    def is_expiring_soon(self):
        if self.end_date:
            return 0 < (self.end_date - timezone.now().date()).days <= 30
        return False
