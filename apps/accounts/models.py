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
        SUPER_ADMIN = 'super_admin', 'Super Admin'
        GYM_MANAGER = 'gym_manager', 'Gym Manager'
        RECEPTIONIST = 'receptionist', 'Receptionist'
        COACH = 'coach', 'Coach'
        MEMBER = 'member', 'Member'

    class Gender(models.TextChoices):
        MALE = 'male', 'Male'
        FEMALE = 'female', 'Female'
        OTHER = 'other', 'Other'

    # Core fields
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    # Personal info
    phone = models.CharField(max_length=20, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    bio = models.TextField(blank=True)

    # Role & permissions
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = 'accounts_users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

    def get_short_name(self):
        return self.first_name or self.username

    @property
    def is_super_admin(self):
        return self.role == self.Role.SUPER_ADMIN

    @property
    def is_gym_manager(self):
        return self.role == self.Role.GYM_MANAGER

    @property
    def is_receptionist(self):
        return self.role == self.Role.RECEPTIONIST

    @property
    def is_coach(self):
        return self.role == self.Role.COACH

    @property
    def is_member(self):
        return self.role == self.Role.MEMBER

    @property
    def can_manage_members(self):
        return self.role in [self.Role.SUPER_ADMIN, self.Role.GYM_MANAGER, self.Role.RECEPTIONIST]

    @property
    def can_view_reports(self):
        return self.role in [self.Role.SUPER_ADMIN, self.Role.GYM_MANAGER]

    @property
    def profile_image_url(self):
        if self.profile_image:
            return self.profile_image.url
        return None

    def get_role_badge_color(self):
        colors = {
            self.Role.SUPER_ADMIN: 'danger',
            self.Role.GYM_MANAGER: 'primary',
            self.Role.RECEPTIONIST: 'success',
            self.Role.COACH: 'warning',
            self.Role.MEMBER: 'info',
        }
        return colors.get(self.role, 'secondary')
