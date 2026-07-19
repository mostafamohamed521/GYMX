from django.db import models
from django.utils import timezone
from apps.accounts.models import User


class MaintenanceSettings(models.Model):
    is_enabled  = models.BooleanField(default=False)
    message     = models.TextField(default="We're performing scheduled maintenance. We'll be back shortly!")
    starts_at   = models.DateTimeField(null=True, blank=True)
    ends_at     = models.DateTimeField(null=True, blank=True)
    updated_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'system_maintenance'
        verbose_name = 'Maintenance Settings'
        verbose_name_plural = 'Maintenance Settings'

    def __str__(self):
        return f"Maintenance Mode: {'ON' if self.is_enabled else 'OFF'}"

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class ReleaseNote(models.Model):
    class ReleaseType(models.TextChoices):
        MAJOR = 'major', 'Major'
        MINOR = 'minor', 'Minor'
        PATCH = 'patch', 'Patch'

    version     = models.CharField(max_length=20, unique=True)
    title       = models.CharField(max_length=200)
    release_type= models.CharField(max_length=6, choices=ReleaseType.choices, default=ReleaseType.MINOR)
    summary     = models.TextField(blank=True)
    changes     = models.JSONField(default=list, help_text='List of change strings')
    released_at = models.DateField(default=timezone.now)

    class Meta:
        db_table = 'system_release_notes'
        ordering = ['-released_at']

    def __str__(self):
        return f"v{self.version} — {self.title}"

    def get_type_color(self):
        return {'major':'red','minor':'blue','patch':'green'}.get(self.release_type,'gray')


class HelpArticle(models.Model):
    class Category(models.TextChoices):
        GETTING_STARTED = 'getting_started', 'Getting Started'
        MEMBERS         = 'members',         'Members'
        PAYMENTS        = 'payments',        'Payments'
        REPORTS         = 'reports',         'Reports'
        TROUBLESHOOTING = 'troubleshooting', 'Troubleshooting'

    title       = models.CharField(max_length=200)
    category    = models.CharField(max_length=16, choices=Category.choices, default=Category.GETTING_STARTED)
    content     = models.TextField()
    order       = models.PositiveIntegerField(default=0)
    views       = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'system_help_articles'
        ordering = ['category', 'order']

    def __str__(self):
        return self.title


class DocPage(models.Model):
    class Section(models.TextChoices):
        OVERVIEW    = 'overview',    'Overview'
        API         = 'api',        'API Reference'
        MODULES     = 'modules',    'Modules'
        ADMIN       = 'admin',      'Administration'

    title       = models.CharField(max_length=200)
    section     = models.CharField(max_length=10, choices=Section.choices, default=Section.OVERVIEW)
    content     = models.TextField()
    order       = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'system_doc_pages'
        ordering = ['section', 'order']

    def __str__(self):
        return self.title
