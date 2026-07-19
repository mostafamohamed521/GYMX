from django.db import models
from django.utils import timezone
from apps.accounts.models import User


class SystemSettings(models.Model):
    """Singleton-style settings row — use SystemSettings.load() to get/create it."""
    # General / Gym Information
    gym_name        = models.CharField(max_length=150, default='GymX')
    logo            = models.ImageField(upload_to='settings/', null=True, blank=True)
    address         = models.TextField(blank=True)
    phone           = models.CharField(max_length=20, blank=True)
    email           = models.EmailField(blank=True)
    website         = models.URLField(blank=True)
    timezone        = models.CharField(max_length=50, default='Africa/Cairo')
    date_format     = models.CharField(max_length=20, default='DD/MM/YYYY')

    # Localization
    default_language = models.CharField(max_length=10, default='en', choices=[('en','English'),('ar','Arabic')])
    default_currency  = models.CharField(max_length=10, default='EGP')
    currency_symbol   = models.CharField(max_length=5, default='EGP')

    # Theme
    primary_color   = models.CharField(max_length=7, default='#3B82F6')
    dark_mode_default = models.BooleanField(default=False)

    # Password Policy
    password_min_length     = models.PositiveIntegerField(default=8)
    password_require_upper  = models.BooleanField(default=True)
    password_require_number = models.BooleanField(default=True)
    password_require_symbol = models.BooleanField(default=False)
    password_expiry_days    = models.PositiveIntegerField(default=90)

    # API
    api_key         = models.CharField(max_length=64, blank=True)
    webhook_url     = models.URLField(blank=True)
    api_rate_limit  = models.PositiveIntegerField(default=1000, help_text='Requests per hour')

    # Email (SMTP)
    smtp_host       = models.CharField(max_length=150, blank=True)
    smtp_port       = models.PositiveIntegerField(default=587)
    smtp_username   = models.CharField(max_length=150, blank=True)
    smtp_from_email = models.EmailField(blank=True)
    email_enabled   = models.BooleanField(default=False)

    # SMS
    sms_provider    = models.CharField(max_length=50, blank=True, default='Twilio')
    sms_api_key     = models.CharField(max_length=100, blank=True)
    sms_sender_id   = models.CharField(max_length=20, blank=True)
    sms_enabled     = models.BooleanField(default=False)

    # Payment Gateway
    payment_provider    = models.CharField(max_length=50, blank=True, default='Stripe')
    payment_public_key  = models.CharField(max_length=150, blank=True)
    payment_test_mode   = models.BooleanField(default=True)

    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'system_settings'
        verbose_name = 'System Settings'
        verbose_name_plural = 'System Settings'

    def __str__(self):
        return f"System Settings ({self.gym_name})"

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class BusinessHours(models.Model):
    class Day(models.IntegerChoices):
        MONDAY    = 0, 'Monday'
        TUESDAY   = 1, 'Tuesday'
        WEDNESDAY = 2, 'Wednesday'
        THURSDAY  = 3, 'Thursday'
        FRIDAY    = 4, 'Friday'
        SATURDAY  = 5, 'Saturday'
        SUNDAY    = 6, 'Sunday'

    day         = models.IntegerField(choices=Day.choices, unique=True)
    is_open     = models.BooleanField(default=True)
    open_time   = models.TimeField(default='06:00')
    close_time  = models.TimeField(default='23:00')

    class Meta:
        db_table = 'business_hours'
        ordering = ['day']

    def __str__(self):
        return f"{self.get_day_display()}: {self.open_time}–{self.close_time}"


class Holiday(models.Model):
    name        = models.CharField(max_length=150)
    date        = models.DateField()
    is_recurring= models.BooleanField(default=False, help_text='Repeats every year (e.g. national holidays)')
    is_closed   = models.BooleanField(default=True, help_text='Gym is closed on this day')
    notes       = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'holidays'
        ordering = ['date']

    def __str__(self):
        return f"{self.name} — {self.date}"

# Note: LoginHistory already exists at apps.accounts.models.LoginHistory — reused, not duplicated.



class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE = 'create', 'Create'
        UPDATE = 'update', 'Update'
        DELETE = 'delete', 'Delete'
        LOGIN  = 'login',  'Login'
        LOGOUT = 'logout', 'Logout'
        EXPORT = 'export', 'Export'

    user        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action      = models.CharField(max_length=8, choices=Action.choices, default=Action.UPDATE)
    model_name  = models.CharField(max_length=100, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    details     = models.TextField(blank=True)
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} — {self.action} — {self.object_repr}"

    def get_action_color(self):
        return {'create':'green','update':'blue','delete':'red','login':'purple','logout':'gray','export':'orange'}.get(self.action,'gray')


class BackupRecord(models.Model):
    class Status(models.TextChoices):
        COMPLETED = 'completed', 'Completed'
        FAILED    = 'failed',    'Failed'
        RUNNING   = 'running',   'Running'

    filename    = models.CharField(max_length=255)
    size_mb     = models.FloatField(default=0)
    status      = models.CharField(max_length=10, choices=Status.choices, default=Status.COMPLETED)
    triggered_by= models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'backup_records'
        ordering = ['-created_at']

    def __str__(self):
        return self.filename

    def get_status_color(self):
        return {'completed':'green','failed':'red','running':'orange'}.get(self.status,'gray')
