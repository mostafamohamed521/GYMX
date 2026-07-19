from django.db import models
from django.utils import timezone
from apps.accounts.models import User
from apps.members.models import Member


class SupportTicket(models.Model):
    class Category(models.TextChoices):
        BILLING     = 'billing',     'Billing'
        MEMBERSHIP  = 'membership',  'Membership'
        FACILITY    = 'facility',    'Facility'
        TECHNICAL   = 'technical',   'Technical'
        OTHER       = 'other',       'Other'

    class Status(models.TextChoices):
        OPEN        = 'open',        'Open'
        IN_PROGRESS = 'in_progress', 'In Progress'
        RESOLVED    = 'resolved',    'Resolved'
        CLOSED      = 'closed',      'Closed'

    member      = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='support_tickets')
    subject     = models.CharField(max_length=200)
    description = models.TextField()
    category    = models.CharField(max_length=12, choices=Category.choices, default=Category.OTHER)
    status      = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    resolution  = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'portal_support_tickets'
        ordering = ['-created_at']

    def __str__(self):
        return f"#{self.pk} — {self.subject}"

    def get_status_color(self):
        return {'open':'red','in_progress':'orange','resolved':'green','closed':'gray'}.get(self.status,'gray')


class TicketReply(models.Model):
    ticket      = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='replies')
    author      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    message     = models.TextField()
    is_staff_reply = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'portal_ticket_replies'
        ordering = ['created_at']


class FreezeRequest(models.Model):
    class Status(models.TextChoices):
        PENDING   = 'pending',   'Pending'
        APPROVED  = 'approved',  'Approved'
        REJECTED  = 'rejected',  'Rejected'

    member      = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='freeze_requests')
    start_date  = models.DateField()
    end_date    = models.DateField()
    reason      = models.TextField(blank=True)
    status      = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'portal_freeze_requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"Freeze — {self.member.get_full_name()} — {self.start_date} to {self.end_date}"

    def get_status_color(self):
        return {'pending':'orange','approved':'green','rejected':'red'}.get(self.status,'gray')

    @property
    def days(self):
        return (self.end_date - self.start_date).days + 1


class RenewalRequest(models.Model):
    class Status(models.TextChoices):
        PENDING   = 'pending',   'Pending'
        APPROVED  = 'approved',  'Approved'
        REJECTED  = 'rejected',  'Rejected'

    member      = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='renewal_requests')
    subscription= models.ForeignKey('memberships.MemberSubscription', on_delete=models.SET_NULL, null=True, blank=True, related_name='renewal_requests')
    requested_plan = models.ForeignKey('memberships.MembershipPlan', on_delete=models.SET_NULL, null=True, blank=True)
    status      = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    notes       = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'portal_renewal_requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"Renewal — {self.member.get_full_name()}"

    def get_status_color(self):
        return {'pending':'orange','approved':'green','rejected':'red'}.get(self.status,'gray')
