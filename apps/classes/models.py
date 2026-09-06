from django.db import models
from django.utils import timezone
from apps.accounts.models import User
from apps.members.models import Member
from apps.coaches.models import Coach


class ClassCategory(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon        = models.CharField(max_length=50, default='fa-dumbbell')
    color       = models.CharField(max_length=7, default='#C80036')

    class Meta:
        db_table = 'class_categories'
        ordering = ['name']
        verbose_name_plural = 'Class Categories'

    def __str__(self):
        return self.name


class GymClass(models.Model):
    class Difficulty(models.TextChoices):
        ALL          = 'all',          'All Levels'
        BEGINNER     = 'beginner',     'Beginner'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED     = 'advanced',     'Advanced'

    class Status(models.TextChoices):
        ACTIVE    = 'active',    'Active'
        INACTIVE  = 'inactive',  'Inactive'
        CANCELLED = 'cancelled', 'Cancelled'

    name            = models.CharField(max_length=200)
    category        = models.ForeignKey(ClassCategory, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='classes')
    coach           = models.ForeignKey(Coach, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='gym_classes')
    description     = models.TextField(blank=True)
    difficulty      = models.CharField(max_length=14, choices=Difficulty.choices,
                                       default=Difficulty.ALL)
    duration_min    = models.PositiveIntegerField(default=60)
    max_capacity    = models.PositiveIntegerField(default=20)
    status          = models.CharField(max_length=12, choices=Status.choices,
                                       default=Status.ACTIVE)
    room            = models.CharField(max_length=100, blank=True)
    equipment_needed= models.TextField(blank=True)
    calories_burn   = models.PositiveIntegerField(default=300)
    color           = models.CharField(max_length=7, default='#C80036')
    image           = models.ImageField(upload_to='classes/', null=True, blank=True)
    created_by      = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'gym_classes'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_status_color(self):
        return {'active':'green','inactive':'gray','cancelled':'red'}.get(self.status,'gray')

    def get_difficulty_color(self):
        return {'all':'blue','beginner':'green','intermediate':'orange','advanced':'red'}.get(self.difficulty,'gray')


class ClassSchedule(models.Model):
    DAYS = [
        (0,'Monday'),(1,'Tuesday'),(2,'Wednesday'),
        (3,'Thursday'),(4,'Friday'),(5,'Saturday'),(6,'Sunday'),
    ]

    gym_class   = models.ForeignKey(GymClass, on_delete=models.CASCADE,
                                    related_name='schedules')
    day_of_week = models.IntegerField(choices=DAYS)
    start_time  = models.TimeField()
    end_time    = models.TimeField()
    is_active   = models.BooleanField(default=True)

    class Meta:
        db_table = 'class_schedules'
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.gym_class.name} — {self.get_day_of_week_display()} {self.start_time}"


class ClassSession(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    gym_class   = models.ForeignKey(GymClass, on_delete=models.CASCADE,
                                    related_name='sessions')
    schedule    = models.ForeignKey(ClassSchedule, on_delete=models.SET_NULL,
                                    null=True, blank=True)
    coach       = models.ForeignKey(Coach, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='class_sessions')
    date        = models.DateField()
    start_time  = models.TimeField()
    end_time    = models.TimeField()
    status      = models.CharField(max_length=12, choices=Status.choices,
                                   default=Status.SCHEDULED)
    notes       = models.TextField(blank=True)
    cancelled_reason = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'class_sessions'
        ordering = ['-date', '-start_time']

    def __str__(self):
        return f"{self.gym_class.name} — {self.date}"

    @property
    def booked_count(self):
        return self.bookings.filter(status='confirmed').count()

    @property
    def available_spots(self):
        return max(self.gym_class.max_capacity - self.booked_count, 0)

    @property
    def is_full(self):
        return self.available_spots == 0

    def get_status_color(self):
        return {
            'scheduled':'blue','in_progress':'green',
            'completed':'purple','cancelled':'red'
        }.get(self.status,'gray')

    @property
    def capacity_pct(self):
        cap = self.gym_class.max_capacity
        return min(int(self.booked_count / max(cap,1) * 100), 100)


class ClassBooking(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = 'confirmed', 'Confirmed'
        WAITLIST  = 'waitlist',  'Waitlist'
        CANCELLED = 'cancelled', 'Cancelled'
        ATTENDED  = 'attended',  'Attended'
        NO_SHOW   = 'no_show',   'No Show'

    session     = models.ForeignKey(ClassSession, on_delete=models.CASCADE,
                                    related_name='bookings')
    member      = models.ForeignKey(Member, on_delete=models.CASCADE,
                                    related_name='class_bookings')
    status      = models.CharField(max_length=12, choices=Status.choices,
                                   default=Status.CONFIRMED)
    booked_at   = models.DateTimeField(auto_now_add=True)
    waitlist_pos= models.PositiveIntegerField(null=True, blank=True)
    notes       = models.TextField(blank=True)
    checked_in  = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'class_bookings'
        unique_together = ['session', 'member']
        ordering = ['-booked_at']

    def __str__(self):
        return f"{self.member.get_full_name()} — {self.session}"

    def get_status_color(self):
        return {
            'confirmed':'green','waitlist':'orange',
            'cancelled':'gray','attended':'blue','no_show':'red'
        }.get(self.status,'gray')


class ClassAttendance(models.Model):
    session     = models.ForeignKey(ClassSession, on_delete=models.CASCADE,
                                    related_name='attendance')
    member      = models.ForeignKey(Member, on_delete=models.CASCADE,
                                    related_name='class_attendance')
    attended    = models.BooleanField(default=True)
    checked_in_at = models.DateTimeField(auto_now_add=True)
    notes       = models.TextField(blank=True)

    class Meta:
        db_table = 'class_attendance'
        unique_together = ['session', 'member']
        ordering = ['-checked_in_at']
