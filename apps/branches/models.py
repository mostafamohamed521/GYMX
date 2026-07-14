from django.db import models
from django.utils import timezone
from apps.accounts.models import User


class Branch(models.Model):
    class Status(models.TextChoices):
        ACTIVE    = 'active',    'Active'
        INACTIVE  = 'inactive',  'Inactive'
        COMING_SOON = 'coming_soon', 'Coming Soon'
        CLOSED    = 'closed',    'Closed'

    name            = models.CharField(max_length=150)
    code            = models.CharField(max_length=10, unique=True, editable=False)
    address         = models.TextField(blank=True)
    city            = models.CharField(max_length=100, blank=True)
    phone           = models.CharField(max_length=20, blank=True)
    email           = models.EmailField(blank=True)
    manager         = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='managed_branches')
    status          = models.CharField(max_length=12, choices=Status.choices,
                                       default=Status.ACTIVE)
    opening_time    = models.TimeField(default='06:00')
    closing_time    = models.TimeField(default='23:00')
    max_capacity    = models.PositiveIntegerField(default=200)
    image           = models.ImageField(upload_to='branches/', null=True, blank=True)
    is_main_branch  = models.BooleanField(default=False)
    latitude        = models.FloatField(null=True, blank=True)
    longitude       = models.FloatField(null=True, blank=True)
    notes           = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'branches'
        ordering = ['-is_main_branch', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.code:
            last = Branch.objects.count() + 1
            self.code = f"BR-{str(last).zfill(3)}"
        super().save(*args, **kwargs)

    def get_status_color(self):
        return {'active':'green','inactive':'gray','coming_soon':'orange','closed':'red'}.get(self.status,'gray')

    @property
    def member_count(self):
        from apps.members.models import Member
        return Member.objects.filter(branch=self).count()

    @property
    def employee_count(self):
        from apps.hr.models import Employee
        return Employee.objects.filter(branch=self).count()


class BranchSettings(models.Model):
    branch          = models.OneToOneField(Branch, on_delete=models.CASCADE, related_name='settings')
    allow_walk_ins  = models.BooleanField(default=True)
    allow_online_booking = models.BooleanField(default=True)
    require_appointment  = models.BooleanField(default=False)
    tax_rate        = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    currency        = models.CharField(max_length=10, default='EGP')
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'branch_settings'

    def __str__(self):
        return f"Settings — {self.branch.name}"


class MemberTransfer(models.Model):
    class Status(models.TextChoices):
        PENDING   = 'pending',   'Pending'
        APPROVED  = 'approved',  'Approved'
        REJECTED  = 'rejected',  'Rejected'

    member          = models.ForeignKey('members.Member', on_delete=models.CASCADE,
                                        related_name='branch_transfers')
    from_branch     = models.ForeignKey(Branch, on_delete=models.SET_NULL,
                                        null=True, related_name='transfers_out')
    to_branch       = models.ForeignKey(Branch, on_delete=models.CASCADE,
                                        related_name='transfers_in')
    reason          = models.TextField(blank=True)
    status          = models.CharField(max_length=10, choices=Status.choices,
                                       default=Status.PENDING)
    requested_by    = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='requested_member_transfers')
    requested_at    = models.DateTimeField(auto_now_add=True)
    processed_at    = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'branch_member_transfers'
        ordering = ['-requested_at']

    def __str__(self):
        return f"{self.member.get_full_name()} — {self.from_branch} → {self.to_branch}"

    def get_status_color(self):
        return {'pending':'orange','approved':'green','rejected':'red'}.get(self.status,'gray')


class EmployeeTransfer(models.Model):
    class Status(models.TextChoices):
        PENDING   = 'pending',   'Pending'
        APPROVED  = 'approved',  'Approved'
        REJECTED  = 'rejected',  'Rejected'

    employee        = models.ForeignKey('hr.Employee', on_delete=models.CASCADE,
                                        related_name='branch_transfers')
    from_branch     = models.ForeignKey(Branch, on_delete=models.SET_NULL,
                                        null=True, related_name='emp_transfers_out')
    to_branch       = models.ForeignKey(Branch, on_delete=models.CASCADE,
                                        related_name='emp_transfers_in')
    reason          = models.TextField(blank=True)
    status          = models.CharField(max_length=10, choices=Status.choices,
                                       default=Status.PENDING)
    requested_by    = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='requested_employee_transfers')
    requested_at    = models.DateTimeField(auto_now_add=True)
    processed_at    = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'branch_employee_transfers'
        ordering = ['-requested_at']

    def __str__(self):
        return f"{self.employee.get_full_name()} — {self.from_branch} → {self.to_branch}"

    def get_status_color(self):
        return {'pending':'orange','approved':'green','rejected':'red'}.get(self.status,'gray')
