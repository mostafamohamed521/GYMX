from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.accounts.models import User
from apps.members.models import Member


# ── Membership Category ────────────────────────────────────
class MembershipCategory(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color       = models.CharField(max_length=7, default='#3B82F6',
                                   help_text='Hex color e.g. #3B82F6')
    icon        = models.CharField(max_length=50, default='fa-id-card',
                                   help_text='Font Awesome icon class')
    is_active   = models.BooleanField(default=True)
    sort_order  = models.PositiveIntegerField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  = 'membership_categories'
        ordering  = ['sort_order', 'name']
        verbose_name_plural = 'Membership Categories'

    def __str__(self):
        return self.name

    def get_active_plans_count(self):
        return self.plans.filter(is_active=True).count()


# ── Membership Plan ────────────────────────────────────────
class MembershipPlan(models.Model):

    class BillingCycle(models.TextChoices):
        DAILY    = 'daily',    'Daily'
        WEEKLY   = 'weekly',   'Weekly'
        MONTHLY  = 'monthly',  'Monthly'
        QUARTERLY= 'quarterly','Quarterly (3 months)'
        BIANNUAL = 'biannual', 'Biannual (6 months)'
        ANNUAL   = 'annual',   'Annual (12 months)'
        LIFETIME = 'lifetime', 'Lifetime'

    class PlanType(models.TextChoices):
        STANDARD    = 'standard',    'Standard'
        PREMIUM     = 'premium',     'Premium'
        VIP         = 'vip',         'VIP'
        STUDENT     = 'student',     'Student'
        SENIOR      = 'senior',      'Senior'
        FAMILY      = 'family',      'Family'
        CORPORATE   = 'corporate',   'Corporate'
        TRIAL       = 'trial',       'Trial'
        CUSTOM      = 'custom',      'Custom'

    category        = models.ForeignKey(MembershipCategory, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='plans')
    name            = models.CharField(max_length=150)
    plan_type       = models.CharField(max_length=15, choices=PlanType.choices,
                                       default=PlanType.STANDARD)
    billing_cycle   = models.CharField(max_length=12, choices=BillingCycle.choices,
                                       default=BillingCycle.MONTHLY)
    duration_days   = models.PositiveIntegerField(default=30,
                                                  help_text='Duration in days')
    price           = models.DecimalField(max_digits=10, decimal_places=2)
    setup_fee       = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    max_freeze_days = models.PositiveIntegerField(default=30)
    max_members     = models.PositiveIntegerField(null=True, blank=True,
                                                  help_text='Max family/corporate members')
    description     = models.TextField(blank=True)
    features        = models.JSONField(default=list, blank=True,
                                       help_text='List of feature strings')
    is_active       = models.BooleanField(default=True)
    is_featured     = models.BooleanField(default=False)
    is_public       = models.BooleanField(default=True,
                                          help_text='Visible to members')
    sort_order      = models.PositiveIntegerField(default=0)
    created_by      = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table  = 'membership_plans'
        ordering  = ['sort_order', 'price']

    def __str__(self):
        return f"{self.name} — {self.get_billing_cycle_display()}"

    @property
    def price_per_day(self):
        if self.duration_days:
            return round(float(self.price) / self.duration_days, 2)
        return None

    @property
    def active_subscriptions_count(self):
        return self.subscriptions.filter(status='active').count()

    def get_type_color(self):
        return {
            'standard':  'blue',
            'premium':   'purple',
            'vip':       'orange',
            'student':   'green',
            'senior':    'cyan',
            'family':    'pink',
            'corporate': 'gray',
            'trial':     'yellow',
            'custom':    'gray',
        }.get(self.plan_type, 'blue')

    def get_cycle_days(self):
        mapping = {
            'daily': 1, 'weekly': 7, 'monthly': 30,
            'quarterly': 90, 'biannual': 180,
            'annual': 365, 'lifetime': 36500,
        }
        return mapping.get(self.billing_cycle, self.duration_days)


# ── Discount ───────────────────────────────────────────────
class Discount(models.Model):
    class DiscountType(models.TextChoices):
        PERCENTAGE = 'percentage', 'Percentage (%)'
        FIXED      = 'fixed',      'Fixed Amount'

    name            = models.CharField(max_length=150)
    discount_type   = models.CharField(max_length=12, choices=DiscountType.choices,
                                       default=DiscountType.PERCENTAGE)
    value           = models.DecimalField(max_digits=8, decimal_places=2,
                                          validators=[MinValueValidator(0)])
    max_discount    = models.DecimalField(max_digits=8, decimal_places=2,
                                          null=True, blank=True,
                                          help_text='Max discount cap for percentage type')
    applicable_plans= models.ManyToManyField(MembershipPlan, blank=True,
                                             related_name='discounts')
    valid_from      = models.DateField(null=True, blank=True)
    valid_until     = models.DateField(null=True, blank=True)
    usage_limit     = models.PositiveIntegerField(null=True, blank=True)
    times_used      = models.PositiveIntegerField(default=0)
    is_active       = models.BooleanField(default=True)
    description     = models.TextField(blank=True)
    created_by      = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'membership_discounts'
        ordering = ['-created_at']

    def __str__(self):
        suffix = '%' if self.discount_type == 'percentage' else ' EGP'
        return f"{self.name} — {self.value}{suffix}"

    def is_valid(self):
        today = timezone.now().date()
        if not self.is_active:
            return False
        if self.valid_from and today < self.valid_from:
            return False
        if self.valid_until and today > self.valid_until:
            return False
        if self.usage_limit and self.times_used >= self.usage_limit:
            return False
        return True

    def calculate(self, amount):
        if self.discount_type == 'percentage':
            disc = float(amount) * float(self.value) / 100
            if self.max_discount:
                disc = min(disc, float(self.max_discount))
        else:
            disc = float(self.value)
        return round(min(disc, float(amount)), 2)


# ── Coupon ─────────────────────────────────────────────────
class Coupon(models.Model):
    code            = models.CharField(max_length=30, unique=True)
    discount        = models.ForeignKey(Discount, on_delete=models.CASCADE,
                                        related_name='coupons')
    member          = models.ForeignKey(Member, on_delete=models.SET_NULL,
                                        null=True, blank=True,
                                        related_name='coupons',
                                        help_text='Leave blank for public coupon')
    is_single_use   = models.BooleanField(default=False)
    times_used      = models.PositiveIntegerField(default=0)
    is_active       = models.BooleanField(default=True)
    valid_until     = models.DateField(null=True, blank=True)
    created_by      = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'membership_coupons'
        ordering = ['-created_at']

    def __str__(self):
        return f"Coupon: {self.code}"

    def is_valid(self):
        if not self.is_active:
            return False
        if self.valid_until and timezone.now().date() > self.valid_until:
            return False
        if self.is_single_use and self.times_used >= 1:
            return False
        return self.discount.is_valid()


# ── Offer ──────────────────────────────────────────────────
class Offer(models.Model):
    class OfferType(models.TextChoices):
        SEASONAL    = 'seasonal',    'Seasonal Offer'
        REFERRAL    = 'referral',    'Referral Bonus'
        BIRTHDAY    = 'birthday',    'Birthday Offer'
        LOYALTY     = 'loyalty',     'Loyalty Reward'
        NEW_MEMBER  = 'new_member',  'New Member Offer'
        BUNDLE      = 'bundle',      'Bundle Deal'
        FLASH       = 'flash',       'Flash Sale'

    name            = models.CharField(max_length=150)
    offer_type      = models.CharField(max_length=15, choices=OfferType.choices)
    description     = models.TextField()
    discount        = models.ForeignKey(Discount, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='offers')
    applicable_plans= models.ManyToManyField(MembershipPlan, blank=True,
                                             related_name='offers')
    banner_image    = models.ImageField(upload_to='offers/', null=True, blank=True)
    valid_from      = models.DateField()
    valid_until     = models.DateField()
    is_active       = models.BooleanField(default=True)
    is_featured     = models.BooleanField(default=False)
    usage_count     = models.PositiveIntegerField(default=0)
    created_by      = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'membership_offers'
        ordering = ['-valid_from']

    def __str__(self):
        return self.name

    @property
    def is_currently_valid(self):
        today = timezone.now().date()
        return self.is_active and self.valid_from <= today <= self.valid_until

    @property
    def days_remaining(self):
        today = timezone.now().date()
        if self.valid_until >= today:
            return (self.valid_until - today).days
        return 0

    def get_type_color(self):
        return {
            'seasonal':   'blue',
            'referral':   'green',
            'birthday':   'pink',
            'loyalty':    'orange',
            'new_member': 'teal',
            'bundle':     'purple',
            'flash':      'red',
        }.get(self.offer_type, 'blue')


# ── Member Subscription ────────────────────────────────────
class MemberSubscription(models.Model):

    class Status(models.TextChoices):
        ACTIVE    = 'active',    'Active'
        EXPIRED   = 'expired',   'Expired'
        FROZEN    = 'frozen',    'Frozen'
        CANCELLED = 'cancelled', 'Cancelled'
        PENDING   = 'pending',   'Pending Payment'
        TRIAL     = 'trial',     'Trial'
        GRACE     = 'grace',     'Grace Period'

    class PaymentStatus(models.TextChoices):
        PAID      = 'paid',    'Paid'
        UNPAID    = 'unpaid',  'Unpaid'
        PARTIAL   = 'partial', 'Partially Paid'
        REFUNDED  = 'refunded','Refunded'
        WAIVED    = 'waived',  'Waived'

    # Core
    member          = models.ForeignKey(Member, on_delete=models.CASCADE,
                                        related_name='subscriptions')
    plan            = models.ForeignKey(MembershipPlan, on_delete=models.PROTECT,
                                        related_name='subscriptions')
    status          = models.CharField(max_length=12, choices=Status.choices,
                                       default=Status.ACTIVE)
    payment_status  = models.CharField(max_length=10, choices=PaymentStatus.choices,
                                       default=PaymentStatus.UNPAID)

    # Dates
    start_date      = models.DateField()
    end_date        = models.DateField()
    activation_date = models.DateField(null=True, blank=True)
    cancelled_at    = models.DateTimeField(null=True, blank=True)
    cancel_reason   = models.TextField(blank=True)

    # Pricing
    original_price  = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_price     = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid     = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon          = models.ForeignKey(Coupon, on_delete=models.SET_NULL,
                                        null=True, blank=True,
                                        related_name='subscriptions')
    discount        = models.ForeignKey(Discount, on_delete=models.SET_NULL,
                                        null=True, blank=True,
                                        related_name='subscriptions')

    # Freeze
    freeze_start    = models.DateField(null=True, blank=True)
    freeze_end      = models.DateField(null=True, blank=True)
    freeze_days_used= models.PositiveIntegerField(default=0)

    # Upgrade/Downgrade
    previous_plan   = models.ForeignKey(MembershipPlan, on_delete=models.SET_NULL,
                                        null=True, blank=True,
                                        related_name='upgraded_from')
    upgrade_type    = models.CharField(max_length=12, blank=True,
                                       choices=[('upgrade','Upgrade'),
                                                ('downgrade','Downgrade'),
                                                ('transfer','Transfer')])

    # Family / Corporate
    parent_subscription = models.ForeignKey('self', on_delete=models.SET_NULL,
                                             null=True, blank=True,
                                             related_name='sub_members')

    # Meta
    notes           = models.TextField(blank=True)
    auto_renew      = models.BooleanField(default=False)
    created_by      = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, blank=True,
                                        related_name='created_subscriptions')
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table  = 'member_subscriptions'
        ordering  = ['-start_date']

    def __str__(self):
        return f"{self.member.get_full_name()} — {self.plan.name} ({self.status})"

    # ── Computed Properties ────────────────────────────────
    @property
    def days_remaining(self):
        today = timezone.now().date()
        if self.status == self.Status.ACTIVE and self.end_date >= today:
            return (self.end_date - today).days
        return 0

    @property
    def days_elapsed(self):
        today = timezone.now().date()
        return max((today - self.start_date).days, 0)

    @property
    def progress_pct(self):
        total = (self.end_date - self.start_date).days
        if total <= 0:
            return 0
        return min(int(self.days_elapsed / total * 100), 100)

    @property
    def amount_due(self):
        return max(float(self.final_price) - float(self.amount_paid), 0)

    @property
    def is_expiring_soon(self):
        return 0 < self.days_remaining <= 7

    @property
    def is_overdue(self):
        return self.status == self.Status.ACTIVE and self.days_remaining == 0

    def get_status_color(self):
        return {
            'active':    'green',
            'expired':   'red',
            'frozen':    'blue',
            'cancelled': 'gray',
            'pending':   'orange',
            'trial':     'cyan',
            'grace':     'yellow',
        }.get(self.status, 'gray')

    def activate(self):
        self.status          = self.Status.ACTIVE
        self.activation_date = timezone.now().date()
        self.save(update_fields=['status', 'activation_date'])

    def cancel(self, reason=''):
        self.status       = self.Status.CANCELLED
        self.cancelled_at = timezone.now()
        self.cancel_reason = reason
        self.save(update_fields=['status', 'cancelled_at', 'cancel_reason'])

    def freeze(self, start, end):
        self.status      = self.Status.FROZEN
        self.freeze_start = start
        self.freeze_end   = end
        self.save(update_fields=['status', 'freeze_start', 'freeze_end'])

    def check_and_update_status(self):
        """Auto-expire if past end date."""
        today = timezone.now().date()
        if self.status == self.Status.ACTIVE and self.end_date < today:
            self.status = self.Status.EXPIRED
            self.save(update_fields=['status'])
        if self.status == self.Status.FROZEN and self.freeze_end and today > self.freeze_end:
            days_frozen = (self.freeze_end - self.freeze_start).days
            self.freeze_days_used += days_frozen
            self.end_date = self.end_date + timezone.timedelta(days=days_frozen)
            self.status   = self.Status.ACTIVE
            self.save(update_fields=['status', 'end_date', 'freeze_days_used',
                                     'freeze_start', 'freeze_end'])


# ── Family Membership ──────────────────────────────────────
class FamilyMembership(models.Model):
    name            = models.CharField(max_length=150)
    primary_member  = models.ForeignKey(Member, on_delete=models.CASCADE,
                                        related_name='family_memberships_primary')
    plan            = models.ForeignKey(MembershipPlan, on_delete=models.PROTECT,
                                        limit_choices_to={'plan_type': 'family'})
    max_members     = models.PositiveIntegerField(default=4)
    discount_per_member = models.DecimalField(max_digits=5, decimal_places=2, default=10,
                                              help_text='% discount per additional member')
    subscription    = models.OneToOneField(MemberSubscription, on_delete=models.CASCADE,
                                           null=True, blank=True,
                                           related_name='family_group')
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'family_memberships'

    def __str__(self):
        return f"Family: {self.name} ({self.primary_member.get_full_name()})"

    @property
    def member_count(self):
        return self.family_members.count() + 1

    @property
    def slots_remaining(self):
        return max(self.max_members - self.member_count, 0)


class FamilyMember(models.Model):
    family          = models.ForeignKey(FamilyMembership, on_delete=models.CASCADE,
                                        related_name='family_members')
    member          = models.ForeignKey(Member, on_delete=models.CASCADE,
                                        related_name='family_member_of')
    relationship    = models.CharField(max_length=50)
    subscription    = models.OneToOneField(MemberSubscription, on_delete=models.SET_NULL,
                                           null=True, blank=True,
                                           related_name='family_member_sub')
    joined_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'family_membership_members'
        unique_together = ['family', 'member']

    def __str__(self):
        return f"{self.member.get_full_name()} in {self.family.name}"


# ── Corporate Membership ───────────────────────────────────
class CorporateMembership(models.Model):
    company_name    = models.CharField(max_length=200)
    company_email   = models.EmailField()
    company_phone   = models.CharField(max_length=20, blank=True)
    company_address = models.TextField(blank=True)
    contact_person  = models.CharField(max_length=150)
    plan            = models.ForeignKey(MembershipPlan, on_delete=models.PROTECT,
                                        limit_choices_to={'plan_type': 'corporate'})
    max_employees   = models.PositiveIntegerField(default=10)
    discount_pct    = models.DecimalField(max_digits=5, decimal_places=2, default=15)
    contract_start  = models.DateField()
    contract_end    = models.DateField()
    is_active       = models.BooleanField(default=True)
    notes           = models.TextField(blank=True)
    created_by      = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'corporate_memberships'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.company_name} — {self.plan.name}"

    @property
    def enrolled_count(self):
        return self.employees.count()

    @property
    def slots_remaining(self):
        return max(self.max_employees - self.enrolled_count, 0)

    @property
    def days_remaining(self):
        today = timezone.now().date()
        if self.contract_end >= today:
            return (self.contract_end - today).days
        return 0


class CorporateEmployee(models.Model):
    corporate       = models.ForeignKey(CorporateMembership, on_delete=models.CASCADE,
                                        related_name='employees')
    member          = models.ForeignKey(Member, on_delete=models.CASCADE,
                                        related_name='corporate_member_of')
    employee_id     = models.CharField(max_length=50, blank=True)
    department      = models.CharField(max_length=100, blank=True)
    subscription    = models.OneToOneField(MemberSubscription, on_delete=models.SET_NULL,
                                           null=True, blank=True,
                                           related_name='corporate_employee_sub')
    enrolled_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'corporate_employees'
        unique_together = ['corporate', 'member']

    def __str__(self):
        return f"{self.member.get_full_name()} @ {self.corporate.company_name}"
