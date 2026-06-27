import random
import string
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError('Username is required')
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.SUPER_ADMIN)
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):

    class Role(models.TextChoices):
        SUPER_ADMIN   = 'super_admin',   'Super Admin'
        GYM_MANAGER   = 'gym_manager',   'Gym Manager'
        RECEPTIONIST  = 'receptionist',  'Receptionist'
        COACH         = 'coach',         'Coach'
        MEMBER        = 'member',        'Member'

    class Gender(models.TextChoices):
        MALE   = 'male',   'Male'
        FEMALE = 'female', 'Female'
        OTHER  = 'other',  'Other'

    class Theme(models.TextChoices):
        LIGHT  = 'light',  'Light'
        DARK   = 'dark',   'Dark'
        SYSTEM = 'system', 'System Default'

    class Language(models.TextChoices):
        EN = 'en', 'English'
        AR = 'ar', 'Arabic'

    # ── Core ─────────────────────────────────────────────
    username      = models.CharField(max_length=150, unique=True)
    email         = models.EmailField(unique=True)
    phone         = models.CharField(max_length=20, blank=True)
    first_name    = models.CharField(max_length=100)
    last_name     = models.CharField(max_length=100)

    # ── Personal ──────────────────────────────────────────
    gender        = models.CharField(max_length=10, choices=Gender.choices, blank=True)
    birth_date    = models.DateField(null=True, blank=True)
    address       = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    bio           = models.TextField(blank=True)
    emergency_contact_name  = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)

    # ── Role & Permissions ────────────────────────────────
    role          = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    is_active     = models.BooleanField(default=True)
    is_staff      = models.BooleanField(default=False)

    # ── Verification ──────────────────────────────────────
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    email_otp         = models.CharField(max_length=6, blank=True)
    phone_otp         = models.CharField(max_length=6, blank=True)
    otp_created_at    = models.DateTimeField(null=True, blank=True)

    # ── 2FA ───────────────────────────────────────────────
    two_fa_enabled = models.BooleanField(default=False)
    two_fa_secret  = models.CharField(max_length=64, blank=True)

    # ── Preferences ───────────────────────────────────────
    theme              = models.CharField(max_length=10, choices=Theme.choices, default=Theme.LIGHT)
    language           = models.CharField(max_length=5, choices=Language.choices, default=Language.EN)
    notif_email        = models.BooleanField(default=True)
    notif_sms          = models.BooleanField(default=False)
    notif_push         = models.BooleanField(default=True)
    notif_payment      = models.BooleanField(default=True)
    notif_membership   = models.BooleanField(default=True)
    notif_attendance   = models.BooleanField(default=False)
    sidebar_collapsed  = models.BooleanField(default=False)

    # ── Security Tracking ─────────────────────────────────
    last_login_ip      = models.GenericIPAddressField(null=True, blank=True)
    failed_login_count = models.PositiveIntegerField(default=0)
    locked_until       = models.DateTimeField(null=True, blank=True)

    # ── Timestamps ────────────────────────────────────────
    date_joined  = models.DateTimeField(default=timezone.now)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    objects = UserManager()
    USERNAME_FIELD  = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table      = 'accounts_users'
        verbose_name  = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

    def get_short_name(self):
        return self.first_name or self.username

    def get_initials(self):
        parts = self.get_full_name().split()
        return ''.join(p[0].upper() for p in parts[:2]) if parts else '?'

    # ── Role helpers ──────────────────────────────────────
    @property
    def is_super_admin(self):   return self.role == self.Role.SUPER_ADMIN
    @property
    def is_gym_manager(self):   return self.role == self.Role.GYM_MANAGER
    @property
    def is_receptionist(self):  return self.role == self.Role.RECEPTIONIST
    @property
    def is_coach(self):         return self.role == self.Role.COACH
    @property
    def is_member_role(self):   return self.role == self.Role.MEMBER

    @property
    def can_manage_members(self):
        return self.role in [self.Role.SUPER_ADMIN, self.Role.GYM_MANAGER, self.Role.RECEPTIONIST]

    @property
    def can_view_reports(self):
        return self.role in [self.Role.SUPER_ADMIN, self.Role.GYM_MANAGER]

    @property
    def profile_image_url(self):
        return self.profile_image.url if self.profile_image else None

    @property
    def is_account_locked(self):
        if self.locked_until and self.locked_until > timezone.now():
            return True
        return False

    def get_role_badge_class(self):
        return {
            self.Role.SUPER_ADMIN:  'red',
            self.Role.GYM_MANAGER:  'blue',
            self.Role.RECEPTIONIST: 'green',
            self.Role.COACH:        'orange',
            self.Role.MEMBER:       'gray',
        }.get(self.role, 'gray')

    def generate_otp(self):
        otp = ''.join(random.choices(string.digits, k=6))
        self.email_otp    = otp
        self.phone_otp    = otp
        self.otp_created_at = timezone.now()
        self.save(update_fields=['email_otp', 'phone_otp', 'otp_created_at'])
        return otp

    def is_otp_valid(self, otp, field='email'):
        if not self.otp_created_at:
            return False
        expired = (timezone.now() - self.otp_created_at).total_seconds() > 600  # 10 min
        if expired:
            return False
        stored = self.email_otp if field == 'email' else self.phone_otp
        return stored == otp

    def clear_otp(self):
        self.email_otp = ''
        self.phone_otp = ''
        self.otp_created_at = None
        self.save(update_fields=['email_otp', 'phone_otp', 'otp_created_at'])


class LoginHistory(models.Model):
    class Status(models.TextChoices):
        SUCCESS = 'success', 'Success'
        FAILED  = 'failed',  'Failed'
        LOGOUT  = 'logout',  'Logout'
        LOCKED  = 'locked',  'Account Locked'

    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    status     = models.CharField(max_length=10, choices=Status.choices, default=Status.SUCCESS)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    location   = models.CharField(max_length=200, blank=True)
    device     = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  = 'accounts_login_history'
        ordering  = ['-created_at']
        verbose_name_plural = 'Login History'

    def __str__(self):
        return f"{self.user.username} — {self.status} — {self.created_at:%Y-%m-%d %H:%M}"

    @property
    def browser(self):
        ua = self.user_agent.lower()
        if 'chrome' in ua:   return 'Chrome'
        if 'firefox' in ua:  return 'Firefox'
        if 'safari' in ua:   return 'Safari'
        if 'edge' in ua:     return 'Edge'
        return 'Unknown'

    @property
    def os(self):
        ua = self.user_agent.lower()
        if 'windows' in ua: return 'Windows'
        if 'mac' in ua:     return 'macOS'
        if 'linux' in ua:   return 'Linux'
        if 'android' in ua: return 'Android'
        if 'iphone' in ua:  return 'iOS'
        return 'Unknown'


class Notification(models.Model):
    class Type(models.TextChoices):
        INFO     = 'info',     'Information'
        SUCCESS  = 'success',  'Success'
        WARNING  = 'warning',  'Warning'
        DANGER   = 'danger',   'Danger'
        PAYMENT  = 'payment',  'Payment'
        MEMBER   = 'member',   'Member'
        SYSTEM   = 'system',   'System'

    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type       = models.CharField(max_length=10, choices=Type.choices, default=Type.INFO)
    title      = models.CharField(max_length=200)
    message    = models.TextField()
    link       = models.CharField(max_length=300, blank=True)
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'accounts_notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.type}] {self.title} → {self.user.username}"

    def get_icon(self):
        return {
            'info':    'fa-circle-info',
            'success': 'fa-circle-check',
            'warning': 'fa-triangle-exclamation',
            'danger':  'fa-circle-xmark',
            'payment': 'fa-credit-card',
            'member':  'fa-user',
            'system':  'fa-gear',
        }.get(self.type, 'fa-bell')

    def get_color(self):
        return {
            'info':    'blue',
            'success': 'green',
            'warning': 'orange',
            'danger':  'red',
            'payment': 'green',
            'member':  'blue',
            'system':  'gray',
        }.get(self.type, 'gray')


class ActivityLog(models.Model):
    class Action(models.TextChoices):
        LOGIN           = 'login',           'Login'
        LOGOUT          = 'logout',          'Logout'
        PROFILE_UPDATE  = 'profile_update',  'Profile Updated'
        PASSWORD_CHANGE = 'password_change', 'Password Changed'
        REGISTER        = 'register',        'Registration'
        MEMBER_ADDED    = 'member_added',    'Member Added'
        MEMBER_UPDATED  = 'member_updated',  'Member Updated'
        PAYMENT_ADDED   = 'payment_added',   'Payment Added'
        SETTINGS_CHANGE = 'settings_change', 'Settings Changed'
        TWO_FA_ENABLED  = '2fa_enabled',     '2FA Enabled'
        TWO_FA_DISABLED = '2fa_disabled',    '2FA Disabled'
        EMAIL_VERIFIED  = 'email_verified',  'Email Verified'
        PHONE_VERIFIED  = 'phone_verified',  'Phone Verified'

    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action      = models.CharField(max_length=30, choices=Action.choices)
    description = models.TextField(blank=True)
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    extra_data  = models.JSONField(default=dict, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'accounts_activity_log'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} — {self.action} — {self.created_at:%Y-%m-%d %H:%M}"

    def get_icon(self):
        return {
            'login':           'fa-right-to-bracket',
            'logout':          'fa-right-from-bracket',
            'profile_update':  'fa-pen-to-square',
            'password_change': 'fa-lock',
            'register':        'fa-user-plus',
            'member_added':    'fa-user-plus',
            'member_updated':  'fa-user-pen',
            'payment_added':   'fa-credit-card',
            'settings_change': 'fa-gear',
            '2fa_enabled':     'fa-shield-halved',
            '2fa_disabled':    'fa-shield',
            'email_verified':  'fa-envelope-circle-check',
            'phone_verified':  'fa-phone',
        }.get(self.action, 'fa-circle-dot')

    def get_color(self):
        return {
            'login':           'green',
            'logout':          'gray',
            'profile_update':  'blue',
            'password_change': 'orange',
            'register':        'blue',
            'member_added':    'blue',
            'payment_added':   'green',
            'settings_change': 'gray',
            '2fa_enabled':     'green',
            '2fa_disabled':    'orange',
            'email_verified':  'green',
            'phone_verified':  'green',
        }.get(self.action, 'gray')


class UserSession(models.Model):
    user         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key  = models.CharField(max_length=40, unique=True)
    ip_address   = models.GenericIPAddressField(null=True, blank=True)
    user_agent   = models.TextField(blank=True)
    is_active    = models.BooleanField(default=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    last_active  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_user_sessions'
        ordering = ['-last_active']

    def __str__(self):
        return f"{self.user.username} — {self.ip_address}"

    @property
    def browser(self):
        ua = self.user_agent.lower()
        if 'chrome' in ua:  return 'Chrome'
        if 'firefox' in ua: return 'Firefox'
        if 'safari' in ua:  return 'Safari'
        if 'edge' in ua:    return 'Edge'
        return 'Browser'

    @property
    def os(self):
        ua = self.user_agent.lower()
        if 'windows' in ua: return 'Windows'
        if 'mac' in ua:     return 'macOS'
        if 'linux' in ua:   return 'Linux'
        if 'android' in ua: return 'Android'
        if 'iphone' in ua:  return 'iOS'
        return 'Unknown OS'

    @property
    def device_icon(self):
        ua = self.user_agent.lower()
        if 'mobile' in ua or 'android' in ua or 'iphone' in ua:
            return 'fa-mobile-screen'
        if 'tablet' in ua or 'ipad' in ua:
            return 'fa-tablet-screen-button'
        return 'fa-desktop'
