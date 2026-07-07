from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.accounts.models import User
from apps.members.models import Member


class CoachSpecialization(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon        = models.CharField(max_length=50, default='fa-dumbbell')
    color       = models.CharField(max_length=7, default='#3B82F6')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'coach_specializations'
        ordering = ['name']

    def __str__(self):
        return self.name


class Coach(models.Model):

    class Status(models.TextChoices):
        ACTIVE    = 'active',    'Active'
        INACTIVE  = 'inactive',  'Inactive'
        ON_LEAVE  = 'on_leave',  'On Leave'
        TERMINATED= 'terminated','Terminated'

    class EmploymentType(models.TextChoices):
        FULL_TIME  = 'full_time',  'Full Time'
        PART_TIME  = 'part_time',  'Part Time'
        FREELANCE  = 'freelance',  'Freelance'
        CONTRACTED = 'contracted', 'Contracted'

    # Personal
    user            = models.OneToOneField(User, on_delete=models.CASCADE,
                                           related_name='coach_profile', null=True, blank=True)
    first_name      = models.CharField(max_length=100)
    last_name       = models.CharField(max_length=100)
    email           = models.EmailField(unique=True)
    phone           = models.CharField(max_length=20)
    phone_secondary = models.CharField(max_length=20, blank=True)
    profile_image   = models.ImageField(upload_to='coaches/', null=True, blank=True)
    gender          = models.CharField(max_length=10,
                                       choices=[('male','Male'),('female','Female')],
                                       default='male')
    birth_date      = models.DateField(null=True, blank=True)
    nationality     = models.CharField(max_length=50, blank=True)
    national_id     = models.CharField(max_length=30, blank=True)
    address         = models.TextField(blank=True)

    # Professional
    status          = models.CharField(max_length=12, choices=Status.choices,
                                       default=Status.ACTIVE)
    employment_type = models.CharField(max_length=12, choices=EmploymentType.choices,
                                       default=EmploymentType.FULL_TIME)
    specializations = models.ManyToManyField(CoachSpecialization, blank=True,
                                             related_name='coaches')
    hire_date       = models.DateField(default=timezone.now)
    experience_years= models.PositiveIntegerField(default=0)
    bio             = models.TextField(blank=True)
    rating          = models.DecimalField(max_digits=3, decimal_places=1, default=5.0,
                                          validators=[MinValueValidator(0), MaxValueValidator(5)])

    # Financial
    base_salary     = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                          help_text='% commission on PT sessions')
    session_rate    = models.DecimalField(max_digits=8, decimal_places=2, default=0,
                                          help_text='Rate per PT session (EGP)')

    # Working hours
    max_members     = models.PositiveIntegerField(default=20)
    max_classes_day = models.PositiveIntegerField(default=4)

    # Social
    instagram       = models.URLField(blank=True)
    youtube         = models.URLField(blank=True)

    # Meta
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'coaches'
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_initials(self):
        return f"{self.first_name[0]}{self.last_name[0]}".upper()

    def get_status_color(self):
        return {
            'active':     'green',
            'inactive':   'gray',
            'on_leave':   'orange',
            'terminated': 'red',
        }.get(self.status, 'gray')

    @property
    def assigned_members_count(self):
        return Member.objects.filter(assigned_coach=self.user).count() if self.user else 0

    @property
    def age(self):
        if self.birth_date:
            today = timezone.now().date()
            return today.year - self.birth_date.year - (
                (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
            )
        return None


class CoachCertificate(models.Model):
    coach       = models.ForeignKey(Coach, on_delete=models.CASCADE,
                                    related_name='certificates')
    title       = models.CharField(max_length=200)
    issued_by   = models.CharField(max_length=200)
    issue_date  = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    document    = models.FileField(upload_to='coach_certs/', null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'coach_certificates'
        ordering = ['-issue_date']

    def __str__(self):
        return f"{self.title} — {self.coach.get_full_name()}"

    @property
    def is_expired(self):
        return self.expiry_date and self.expiry_date < timezone.now().date()

    @property
    def is_expiring_soon(self):
        if self.expiry_date:
            return 0 < (self.expiry_date - timezone.now().date()).days <= 30
        return False


class CoachNote(models.Model):
    class Priority(models.TextChoices):
        LOW    = 'low',    'Low'
        NORMAL = 'normal', 'Normal'
        HIGH   = 'high',   'High'

    coach       = models.ForeignKey(Coach, on_delete=models.CASCADE, related_name='notes')
    title       = models.CharField(max_length=200)
    body        = models.TextField()
    priority    = models.CharField(max_length=8, choices=Priority.choices, default=Priority.NORMAL)
    is_pinned   = models.BooleanField(default=False)
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'coach_notes'
        ordering = ['-is_pinned', '-created_at']

    def get_priority_color(self):
        return {'low':'gray','normal':'blue','high':'red'}.get(self.priority,'blue')


class CoachAvailability(models.Model):
    DAYS = [(0,'Monday'),(1,'Tuesday'),(2,'Wednesday'),(3,'Thursday'),
            (4,'Friday'),(5,'Saturday'),(6,'Sunday')]

    coach       = models.ForeignKey(Coach, on_delete=models.CASCADE,
                                    related_name='availability')
    day_of_week = models.IntegerField(choices=DAYS)
    start_time  = models.TimeField()
    end_time    = models.TimeField()
    is_available= models.BooleanField(default=True)

    class Meta:
        db_table  = 'coach_availability'
        ordering  = ['day_of_week', 'start_time']
        unique_together = ['coach', 'day_of_week']

    def __str__(self):
        return f"{self.coach.get_full_name()} — {self.get_day_of_week_display()}"


class CoachSchedule(models.Model):
    class SessionType(models.TextChoices):
        CLASS   = 'class',   'Group Class'
        PT      = 'pt',      'Personal Training'
        MEETING = 'meeting', 'Meeting'
        BREAK   = 'break',   'Break'
        OTHER   = 'other',   'Other'

    coach       = models.ForeignKey(Coach, on_delete=models.CASCADE,
                                    related_name='schedule_entries')
    session_type= models.CharField(max_length=10, choices=SessionType.choices,
                                   default=SessionType.PT)
    title       = models.CharField(max_length=200)
    date        = models.DateField()
    start_time  = models.TimeField()
    end_time    = models.TimeField()
    member      = models.ForeignKey(Member, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='coach_sessions')
    notes       = models.TextField(blank=True)
    is_completed= models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'coach_schedule'
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.coach.get_full_name()} — {self.title} ({self.date})"

    def get_type_color(self):
        return {
            'class':'blue','pt':'green','meeting':'orange',
            'break':'gray','other':'purple',
        }.get(self.session_type,'blue')


class CoachAttendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = 'present', 'Present'
        ABSENT  = 'absent',  'Absent'
        LATE    = 'late',    'Late'
        LEAVE   = 'leave',   'Leave'

    coach       = models.ForeignKey(Coach, on_delete=models.CASCADE,
                                    related_name='attendance')
    date        = models.DateField()
    status      = models.CharField(max_length=10, choices=Status.choices,
                                   default=Status.PRESENT)
    check_in    = models.TimeField(null=True, blank=True)
    check_out   = models.TimeField(null=True, blank=True)
    notes       = models.TextField(blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                    null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'coach_attendance'
        unique_together = ['coach', 'date']
        ordering = ['-date']

    def get_status_color(self):
        return {'present':'green','absent':'red','late':'orange','leave':'blue'}.get(self.status,'gray')


class CoachSalary(models.Model):
    class Status(models.TextChoices):
        PENDING  = 'pending',  'Pending'
        PAID     = 'paid',     'Paid'
        PARTIAL  = 'partial',  'Partially Paid'
        CANCELLED= 'cancelled','Cancelled'

    coach           = models.ForeignKey(Coach, on_delete=models.CASCADE,
                                        related_name='salaries')
    month           = models.DateField(help_text='First day of salary month')
    base_salary     = models.DecimalField(max_digits=10, decimal_places=2)
    bonus           = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commissions     = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_salary      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status          = models.CharField(max_length=12, choices=Status.choices,
                                       default=Status.PENDING)
    paid_date       = models.DateField(null=True, blank=True)
    notes           = models.TextField(blank=True)
    created_by      = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'coach_salaries'
        ordering = ['-month']
        unique_together = ['coach', 'month']

    def __str__(self):
        return f"{self.coach.get_full_name()} — {self.month.strftime('%B %Y')}"

    def save(self, *args, **kwargs):
        self.net_salary = (
            float(self.base_salary) + float(self.bonus) +
            float(self.commissions) - float(self.deductions)
        )
        super().save(*args, **kwargs)

    def get_status_color(self):
        return {'pending':'orange','paid':'green','partial':'blue','cancelled':'gray'}.get(self.status,'gray')


class CoachCommission(models.Model):
    coach       = models.ForeignKey(Coach, on_delete=models.CASCADE,
                                    related_name='commissions')
    member      = models.ForeignKey(Member, on_delete=models.CASCADE,
                                    related_name='coach_commissions')
    description = models.CharField(max_length=200)
    amount      = models.DecimalField(max_digits=10, decimal_places=2)
    date        = models.DateField(default=timezone.now)
    is_paid     = models.BooleanField(default=False)
    notes       = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'coach_commissions'
        ordering = ['-date']

    def __str__(self):
        return f"{self.coach.get_full_name()} — {self.amount} EGP"
