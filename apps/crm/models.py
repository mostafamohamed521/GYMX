from django.db import models
from django.utils import timezone
from apps.accounts.models import User
from apps.members.models import Member


class Lead(models.Model):
    class Source(models.TextChoices):
        WALK_IN   = 'walk_in',   'Walk-in'
        PHONE     = 'phone',     'Phone Call'
        SOCIAL    = 'social',    'Social Media'
        REFERRAL  = 'referral',  'Referral'
        WEBSITE   = 'website',   'Website'
        OTHER     = 'other',     'Other'

    class Status(models.TextChoices):
        NEW         = 'new',         'New'
        CONTACTED   = 'contacted',   'Contacted'
        QUALIFIED   = 'qualified',   'Qualified'
        CONVERTED   = 'converted',   'Converted'
        LOST        = 'lost',        'Lost'

    first_name  = models.CharField(max_length=100)
    last_name   = models.CharField(max_length=100)
    phone       = models.CharField(max_length=20)
    email       = models.EmailField(blank=True)
    source      = models.CharField(max_length=10, choices=Source.choices, default=Source.WALK_IN)
    status      = models.CharField(max_length=10, choices=Status.choices, default=Status.NEW)
    interest    = models.CharField(max_length=200, blank=True, help_text='e.g. Weight loss, PT sessions')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='assigned_leads')
    converted_member = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='lead_source')
    notes       = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'crm_leads'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_initials(self):
        return f"{self.first_name[0]}{self.last_name[0]}".upper()

    def get_status_color(self):
        return {'new':'blue','contacted':'orange','qualified':'purple','converted':'green','lost':'red'}.get(self.status,'gray')

    def get_source_icon(self):
        return {
            'walk_in':'fa-door-open','phone':'fa-phone','social':'fa-hashtag',
            'referral':'fa-user-plus','website':'fa-globe','other':'fa-ellipsis',
        }.get(self.source,'fa-circle-question')


class FollowUp(models.Model):
    class Status(models.TextChoices):
        PENDING   = 'pending',   'Pending'
        DONE      = 'done',      'Done'
        MISSED    = 'missed',    'Missed'

    lead        = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='follow_ups')
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField(default='10:00')
    notes       = models.TextField(blank=True)
    status      = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    completed_at= models.DateTimeField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'crm_follow_ups'
        ordering = ['scheduled_date', 'scheduled_time']

    def __str__(self):
        return f"Follow-up — {self.lead.get_full_name()} — {self.scheduled_date}"

    def get_status_color(self):
        return {'pending':'orange','done':'green','missed':'red'}.get(self.status,'gray')


class CallLog(models.Model):
    class Direction(models.TextChoices):
        INBOUND  = 'inbound',  'Inbound'
        OUTBOUND = 'outbound', 'Outbound'

    class Outcome(models.TextChoices):
        ANSWERED    = 'answered',    'Answered'
        NO_ANSWER   = 'no_answer',   'No Answer'
        VOICEMAIL   = 'voicemail',   'Left Voicemail'
        BUSY        = 'busy',        'Busy'

    lead        = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='calls')
    member      = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True, related_name='calls')
    direction   = models.CharField(max_length=10, choices=Direction.choices, default=Direction.OUTBOUND)
    outcome     = models.CharField(max_length=12, choices=Outcome.choices, default=Outcome.ANSWERED)
    duration_min= models.PositiveIntegerField(default=0)
    notes       = models.TextField(blank=True)
    called_by   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    called_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'crm_call_logs'
        ordering = ['-called_at']

    def __str__(self):
        target = self.lead.get_full_name() if self.lead else (self.member.get_full_name() if self.member else 'Unknown')
        return f"Call — {target} — {self.called_at:%Y-%m-%d}"

    def get_outcome_color(self):
        return {'answered':'green','no_answer':'orange','voicemail':'blue','busy':'red'}.get(self.outcome,'gray')


class Meeting(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        NO_SHOW   = 'no_show',   'No Show'

    lead        = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='meetings')
    member      = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True, related_name='meetings')
    title       = models.CharField(max_length=200)
    date        = models.DateField()
    start_time  = models.TimeField()
    end_time    = models.TimeField()
    location    = models.CharField(max_length=200, blank=True)
    status      = models.CharField(max_length=10, choices=Status.choices, default=Status.SCHEDULED)
    notes       = models.TextField(blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'crm_meetings'
        ordering = ['-date', '-start_time']

    def __str__(self):
        return self.title

    def get_status_color(self):
        return {'scheduled':'blue','completed':'green','cancelled':'gray','no_show':'red'}.get(self.status,'gray')


class Feedback(models.Model):
    class Category(models.TextChoices):
        FACILITY   = 'facility',   'Facility'
        STAFF      = 'staff',      'Staff'
        CLASSES    = 'classes',    'Classes'
        EQUIPMENT  = 'equipment',  'Equipment'
        GENERAL    = 'general',    'General'

    member      = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedback_entries')
    category    = models.CharField(max_length=10, choices=Category.choices, default=Category.GENERAL)
    rating      = models.PositiveIntegerField(default=5)
    comments    = models.TextField(blank=True)
    submitted_at= models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'crm_feedback'
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Feedback — {self.member.get_full_name() if self.member else 'Anonymous'} — {self.rating}★"


class Complaint(models.Model):
    class Priority(models.TextChoices):
        LOW    = 'low',    'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH   = 'high',   'High'
        URGENT = 'urgent', 'Urgent'

    class Status(models.TextChoices):
        OPEN        = 'open',        'Open'
        IN_PROGRESS = 'in_progress', 'In Progress'
        RESOLVED    = 'resolved',    'Resolved'
        CLOSED      = 'closed',      'Closed'

    member      = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True, related_name='complaints')
    subject     = models.CharField(max_length=200)
    description = models.TextField()
    priority    = models.CharField(max_length=8, choices=Priority.choices, default=Priority.MEDIUM)
    status      = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='assigned_complaints')
    resolution  = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'crm_complaints'
        ordering = ['-created_at']

    def __str__(self):
        return self.subject

    def get_priority_color(self):
        return {'low':'gray','medium':'blue','high':'orange','urgent':'red'}.get(self.priority,'gray')

    def get_status_color(self):
        return {'open':'red','in_progress':'orange','resolved':'green','closed':'gray'}.get(self.status,'gray')


class Suggestion(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = 'submitted', 'Submitted'
        REVIEWING = 'reviewing', 'Under Review'
        APPROVED  = 'approved',  'Approved'
        REJECTED  = 'rejected',  'Rejected'
        IMPLEMENTED = 'implemented', 'Implemented'

    member      = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True, related_name='suggestions')
    title       = models.CharField(max_length=200)
    description = models.TextField()
    status      = models.CharField(max_length=12, choices=Status.choices, default=Status.SUBMITTED)
    votes       = models.PositiveIntegerField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'crm_suggestions'
        ordering = ['-votes', '-created_at']

    def __str__(self):
        return self.title

    def get_status_color(self):
        return {'submitted':'blue','reviewing':'orange','approved':'green','rejected':'red','implemented':'purple'}.get(self.status,'gray')


class LoyaltyTier(models.Model):
    name           = models.CharField(max_length=50)
    min_points     = models.PositiveIntegerField()
    color          = models.CharField(max_length=7, default='#F59E0B')
    perks          = models.TextField(blank=True)

    class Meta:
        db_table = 'crm_loyalty_tiers'
        ordering = ['min_points']

    def __str__(self):
        return self.name


class LoyaltyAccount(models.Model):
    member      = models.OneToOneField(Member, on_delete=models.CASCADE, related_name='loyalty_account')
    points      = models.PositiveIntegerField(default=0)
    tier        = models.ForeignKey(LoyaltyTier, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'crm_loyalty_accounts'
        ordering = ['-points']

    def __str__(self):
        return f"{self.member.get_full_name()} — {self.points} pts"


class LoyaltyTransaction(models.Model):
    class TxType(models.TextChoices):
        EARNED   = 'earned',   'Earned'
        REDEEMED = 'redeemed', 'Redeemed'

    account     = models.ForeignKey(LoyaltyAccount, on_delete=models.CASCADE, related_name='transactions')
    tx_type     = models.CharField(max_length=10, choices=TxType.choices, default=TxType.EARNED)
    points      = models.IntegerField()
    reason      = models.CharField(max_length=200, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'crm_loyalty_transactions'
        ordering = ['-created_at']


class Referral(models.Model):
    class Status(models.TextChoices):
        PENDING   = 'pending',   'Pending'
        CONVERTED = 'converted', 'Converted'
        EXPIRED   = 'expired',   'Expired'

    referrer    = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='referrals_made')
    referred_name  = models.CharField(max_length=200)
    referred_phone = models.CharField(max_length=20, blank=True)
    referred_member = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='referred_by_entry')
    status      = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    reward_points = models.PositiveIntegerField(default=100)
    reward_given= models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'crm_referrals'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.referrer.get_full_name()} → {self.referred_name}"

    def get_status_color(self):
        return {'pending':'orange','converted':'green','expired':'gray'}.get(self.status,'gray')


class Campaign(models.Model):
    class Channel(models.TextChoices):
        EMAIL = 'email', 'Email'
        SMS   = 'sms',   'SMS'
        BOTH  = 'both',  'Email & SMS'

    class Status(models.TextChoices):
        DRAFT     = 'draft',     'Draft'
        SCHEDULED = 'scheduled', 'Scheduled'
        SENT      = 'sent',      'Sent'
        CANCELLED = 'cancelled', 'Cancelled'

    name        = models.CharField(max_length=200)
    channel     = models.CharField(max_length=6, choices=Channel.choices, default=Channel.EMAIL)
    subject     = models.CharField(max_length=200, blank=True)
    message     = models.TextField()
    target_audience = models.CharField(max_length=200, blank=True, help_text='e.g. All active members, Leads only')
    status      = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    scheduled_at= models.DateTimeField(null=True, blank=True)
    sent_at     = models.DateTimeField(null=True, blank=True)
    recipients_count = models.PositiveIntegerField(default=0)
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'crm_campaigns'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_status_color(self):
        return {'draft':'gray','scheduled':'blue','sent':'green','cancelled':'red'}.get(self.status,'gray')
