from django.db import models
from django.utils import timezone


class AttendanceSettings(models.Model):
    gym_open_time        = models.TimeField(default='06:00')
    gym_close_time       = models.TimeField(default='23:00')
    max_session_hours    = models.PositiveIntegerField(default=4)
    late_threshold_min   = models.PositiveIntegerField(default=30)
    require_membership   = models.BooleanField(default=True)
    allow_multiple_checkin = models.BooleanField(default=False)
    updated_at           = models.DateTimeField(auto_now=True)

    class Meta:
        db_table     = 'attendance_settings'
        verbose_name = 'Attendance Settings'

    def __str__(self):
        return 'Attendance Settings'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class AttendanceSession(models.Model):
    date       = models.DateField(default=timezone.now)
    is_open    = models.BooleanField(default=True)
    opened_at  = models.DateTimeField(auto_now_add=True)
    closed_at  = models.DateTimeField(null=True, blank=True)
    notes      = models.TextField(blank=True)

    class Meta:
        db_table = 'attendance_sessions'
        ordering = ['-date']

    def __str__(self):
        return f"Session {self.date}"

    @property
    def total_visitors(self):
        return self.records.values('member').distinct().count()


class AttendanceRecord(models.Model):

    class CheckInMethod(models.TextChoices):
        QR      = 'qr',      'QR Code'
        BARCODE = 'barcode', 'Barcode'
        MANUAL  = 'manual',  'Manual'
        FACE    = 'face',    'Face Recognition'
        APP     = 'app',     'Mobile App'

    class Status(models.TextChoices):
        PRESENT = 'present', 'Present'
        LATE    = 'late',    'Late'
        LEFT    = 'left',    'Left Early'

    # FK strings to avoid circular imports
    member      = models.ForeignKey(
        'members.Member', on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    session     = models.ForeignKey(
        AttendanceSession, on_delete=models.CASCADE,
        related_name='records', null=True, blank=True
    )
    recorded_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='recorded_attendance'
    )

    date             = models.DateField(default=timezone.now)
    check_in         = models.DateTimeField(null=True, blank=True)
    check_out        = models.DateTimeField(null=True, blank=True)
    check_in_method  = models.CharField(max_length=10, choices=CheckInMethod.choices,
                                        default=CheckInMethod.MANUAL)
    check_out_method = models.CharField(max_length=10, choices=CheckInMethod.choices,
                                        blank=True)
    status           = models.CharField(max_length=10, choices=Status.choices,
                                        default=Status.PRESENT)
    notes            = models.TextField(blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'attendance_records'
        ordering = ['-check_in']
        indexes  = [
            models.Index(fields=['date', 'member']),
            models.Index(fields=['check_in']),
        ]

    def __str__(self):
        return f"{self.member} — {self.date}"

    @property
    def duration_minutes(self):
        if self.check_in and self.check_out:
            return int((self.check_out - self.check_in).total_seconds() // 60)
        return None

    @property
    def duration_display(self):
        mins = self.duration_minutes
        if mins is None:
            if self.check_in:
                mins = int((timezone.now() - self.check_in).total_seconds() // 60)
                h, m = divmod(mins, 60)
                return f"{h}h {m}m (ongoing)"
            return '—'
        h, m = divmod(mins, 60)
        return f"{h}h {m}m" if h else f"{m}m"

    @property
    def is_inside(self):
        return self.check_in is not None and self.check_out is None

    def get_status_color(self):
        return {'present': 'green', 'late': 'orange', 'left': 'blue'}.get(self.status, 'gray')

    def get_method_icon(self):
        return {
            'qr': 'fa-qrcode', 'barcode': 'fa-barcode',
            'manual': 'fa-hand-pointer', 'face': 'fa-face-smile',
            'app': 'fa-mobile-screen',
        }.get(self.check_in_method, 'fa-clock')

    def do_checkout(self, method='manual', recorded_by=None):
        self.check_out        = timezone.now()
        self.check_out_method = method
        if recorded_by:
            self.recorded_by = recorded_by
        self.save(update_fields=['check_out', 'check_out_method', 'recorded_by'])
