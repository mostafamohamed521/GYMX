from django.db import models
from django.utils import timezone
from apps.accounts.models import User
from apps.members.models import Member

# Note: the actual Notification model already exists at apps.accounts.models.Notification
# (used app-wide for the notification bell). This app reuses it rather than duplicating it.



class EmailTemplate(models.Model):
    class Purpose(models.TextChoices):
        WELCOME       = 'welcome',       'Welcome'
        RENEWAL       = 'renewal',       'Renewal Reminder'
        EXPIRY        = 'expiry',        'Expiry Alert'
        PAYMENT       = 'payment',       'Payment Reminder'
        BIRTHDAY      = 'birthday',      'Birthday'
        ANNOUNCEMENT  = 'announcement',  'Announcement'
        CUSTOM        = 'custom',        'Custom'

    name        = models.CharField(max_length=150)
    purpose     = models.CharField(max_length=12, choices=Purpose.choices, default=Purpose.CUSTOM)
    subject     = models.CharField(max_length=200)
    body        = models.TextField(help_text='Use {{member_name}}, {{gym_name}}, {{expiry_date}} etc as placeholders')
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notif_email_templates'
        ordering = ['name']

    def __str__(self):
        return self.name


class SMSTemplate(models.Model):
    class Purpose(models.TextChoices):
        WELCOME       = 'welcome',       'Welcome'
        RENEWAL       = 'renewal',       'Renewal Reminder'
        EXPIRY        = 'expiry',        'Expiry Alert'
        PAYMENT       = 'payment',       'Payment Reminder'
        BIRTHDAY      = 'birthday',      'Birthday'
        CUSTOM        = 'custom',        'Custom'

    name        = models.CharField(max_length=150)
    purpose     = models.CharField(max_length=12, choices=Purpose.choices, default=Purpose.CUSTOM)
    body        = models.CharField(max_length=320, help_text='Keep under 160 chars for single SMS segment')
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notif_sms_templates'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def char_count(self):
        return len(self.body)


class PushNotification(models.Model):
    class Status(models.TextChoices):
        DRAFT     = 'draft',     'Draft'
        SCHEDULED = 'scheduled', 'Scheduled'
        SENT      = 'sent',      'Sent'

    title       = models.CharField(max_length=150)
    message     = models.CharField(max_length=250)
    target_audience = models.CharField(max_length=200, default='All members')
    status      = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    scheduled_at= models.DateTimeField(null=True, blank=True)
    sent_at     = models.DateTimeField(null=True, blank=True)
    recipients_count = models.PositiveIntegerField(default=0)
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notif_push'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_status_color(self):
        return {'draft':'gray','scheduled':'blue','sent':'green'}.get(self.status,'gray')


class Announcement(models.Model):
    class Priority(models.TextChoices):
        LOW    = 'low',    'Low'
        NORMAL = 'normal', 'Normal'
        HIGH   = 'high',   'High'

    title       = models.CharField(max_length=200)
    body        = models.TextField()
    priority    = models.CharField(max_length=6, choices=Priority.choices, default=Priority.NORMAL)
    is_pinned   = models.BooleanField(default=False)
    is_active   = models.BooleanField(default=True)
    starts_at   = models.DateTimeField(default=timezone.now)
    ends_at     = models.DateTimeField(null=True, blank=True)
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notif_announcements'
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return self.title

    def get_priority_color(self):
        return {'low':'gray','normal':'blue','high':'red'}.get(self.priority,'gray')


class ScheduledMessage(models.Model):
    class Channel(models.TextChoices):
        EMAIL = 'email', 'Email'
        SMS   = 'sms',   'SMS'
        PUSH  = 'push',  'Push'

    class Status(models.TextChoices):
        PENDING   = 'pending',   'Pending'
        SENT      = 'sent',      'Sent'
        CANCELLED = 'cancelled', 'Cancelled'
        FAILED    = 'failed',    'Failed'

    name        = models.CharField(max_length=200)
    channel     = models.CharField(max_length=5, choices=Channel.choices, default=Channel.EMAIL)
    target_audience = models.CharField(max_length=200, default='All members')
    message     = models.TextField()
    scheduled_for = models.DateTimeField()
    status      = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notif_scheduled_messages'
        ordering = ['scheduled_for']

    def __str__(self):
        return self.name

    def get_status_color(self):
        return {'pending':'orange','sent':'green','cancelled':'gray','failed':'red'}.get(self.status,'gray')

    def get_channel_icon(self):
        return {'email':'fa-envelope','sms':'fa-comment-sms','push':'fa-bell'}.get(self.channel,'fa-paper-plane')
