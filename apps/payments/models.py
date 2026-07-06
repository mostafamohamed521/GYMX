from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from apps.accounts.models import User
from apps.members.models import Member
from apps.memberships.models import MemberSubscription


def invoice_number():
    from django.utils import timezone
    prefix = timezone.now().strftime('%Y%m')
    last   = Invoice.objects.filter(invoice_number__startswith=f'INV-{prefix}').count()
    return f'INV-{prefix}-{str(last + 1).zfill(4)}'


def receipt_number():
    from django.utils import timezone
    prefix = timezone.now().strftime('%Y%m')
    last   = Receipt.objects.filter(receipt_number__startswith=f'RCP-{prefix}').count()
    return f'RCP-{prefix}-{str(last + 1).zfill(4)}'


# ── Invoice ────────────────────────────────────────────────
class Invoice(models.Model):

    class Status(models.TextChoices):
        DRAFT    = 'draft',    'Draft'
        SENT     = 'sent',     'Sent'
        PAID     = 'paid',     'Paid'
        PARTIAL  = 'partial',  'Partially Paid'
        OVERDUE  = 'overdue',  'Overdue'
        CANCELLED= 'cancelled','Cancelled'
        REFUNDED = 'refunded', 'Refunded'

    invoice_number  = models.CharField(max_length=30, unique=True, editable=False)
    member          = models.ForeignKey(Member, on_delete=models.CASCADE,
                                        related_name='invoices')
    subscription    = models.ForeignKey(MemberSubscription, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='invoices')
    status          = models.CharField(max_length=12, choices=Status.choices,
                                       default=Status.DRAFT)
    issue_date      = models.DateField(default=timezone.now)
    due_date        = models.DateField()
    subtotal        = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total           = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_paid     = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes           = models.TextField(blank=True)
    created_by      = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='created_invoices')
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'invoices'
        ordering = ['-issue_date']

    def __str__(self):
        return f"{self.invoice_number} — {self.member.get_full_name()}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = invoice_number()
        super().save(*args, **kwargs)

    @property
    def amount_due(self):
        return max(float(self.total) - float(self.amount_paid), 0)

    @property
    def is_overdue(self):
        return self.status not in ('paid','cancelled','refunded') and self.due_date < timezone.now().date()

    def get_status_color(self):
        return {
            'draft':    'gray',
            'sent':     'blue',
            'paid':     'green',
            'partial':  'orange',
            'overdue':  'red',
            'cancelled':'gray',
            'refunded': 'purple',
        }.get(self.status, 'gray')


# ── Invoice Line Item ──────────────────────────────────────
class InvoiceItem(models.Model):
    invoice     = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=255)
    quantity    = models.PositiveIntegerField(default=1)
    unit_price  = models.DecimalField(max_digits=10, decimal_places=2)
    total       = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'invoice_items'

    def save(self, *args, **kwargs):
        self.total = float(self.quantity) * float(self.unit_price)
        super().save(*args, **kwargs)


# ── Payment ────────────────────────────────────────────────
class Payment(models.Model):

    class Method(models.TextChoices):
        CASH    = 'cash',    'Cash'
        CARD    = 'card',    'Credit/Debit Card'
        TRANSFER= 'transfer','Bank Transfer'
        ONLINE  = 'online',  'Online Payment'
        CHEQUE  = 'cheque',  'Cheque'
        WALLET  = 'wallet',  'Digital Wallet'

    class Status(models.TextChoices):
        PENDING   = 'pending',   'Pending'
        COMPLETED = 'completed', 'Completed'
        FAILED    = 'failed',    'Failed'
        REFUNDED  = 'refunded',  'Refunded'
        CANCELLED = 'cancelled', 'Cancelled'

    class PaymentType(models.TextChoices):
        MEMBERSHIP  = 'membership',  'Membership Fee'
        REGISTRATION= 'registration','Registration Fee'
        PERSONAL    = 'personal',    'Personal Training'
        SUPPLEMENT  = 'supplement',  'Supplements'
        LOCKER      = 'locker',      'Locker Fee'
        LATE_FEE    = 'late_fee',    'Late Fee'
        OTHER       = 'other',       'Other'

    member          = models.ForeignKey(Member, on_delete=models.CASCADE,
                                        related_name='payments')
    invoice         = models.ForeignKey(Invoice, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='payments')
    subscription    = models.ForeignKey(MemberSubscription, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='payment_records')
    payment_type    = models.CharField(max_length=15, choices=PaymentType.choices,
                                       default=PaymentType.MEMBERSHIP)
    method          = models.CharField(max_length=10, choices=Method.choices,
                                       default=Method.CASH)
    status          = models.CharField(max_length=12, choices=Status.choices,
                                       default=Status.COMPLETED)
    amount          = models.DecimalField(max_digits=10, decimal_places=2,
                                          validators=[MinValueValidator(0)])
    discount        = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax             = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reference       = models.CharField(max_length=100, blank=True,
                                       help_text='Transaction/reference number')
    payment_date    = models.DateField(default=timezone.now)
    payment_time    = models.TimeField(default=timezone.now)
    notes           = models.TextField(blank=True)
    received_by     = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='received_payments')
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payments'
        ordering = ['-payment_date', '-created_at']

    def __str__(self):
        return f"{self.member.get_full_name()} — {self.amount} EGP ({self.get_method_display()})"

    def save(self, *args, **kwargs):
        self.net_amount = float(self.amount) - float(self.discount) + float(self.tax)
        super().save(*args, **kwargs)

    def get_status_color(self):
        return {
            'pending':   'orange',
            'completed': 'green',
            'failed':    'red',
            'refunded':  'purple',
            'cancelled': 'gray',
        }.get(self.status, 'gray')

    def get_method_icon(self):
        return {
            'cash':     'fa-money-bill-wave',
            'card':     'fa-credit-card',
            'transfer': 'fa-building-columns',
            'online':   'fa-globe',
            'cheque':   'fa-file-invoice',
            'wallet':   'fa-wallet',
        }.get(self.method, 'fa-coins')


# ── Receipt ────────────────────────────────────────────────
class Receipt(models.Model):
    receipt_number  = models.CharField(max_length=30, unique=True, editable=False)
    payment         = models.OneToOneField(Payment, on_delete=models.CASCADE,
                                           related_name='receipt')
    issued_at       = models.DateTimeField(auto_now_add=True)
    issued_by       = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, blank=True)

    class Meta:
        db_table = 'receipts'
        ordering = ['-issued_at']

    def __str__(self):
        return f"Receipt {self.receipt_number}"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = receipt_number()
        super().save(*args, **kwargs)


# ── Installment Plan ───────────────────────────────────────
class InstallmentPlan(models.Model):

    class Status(models.TextChoices):
        ACTIVE    = 'active',    'Active'
        COMPLETED = 'completed', 'Completed'
        DEFAULTED = 'defaulted', 'Defaulted'
        CANCELLED = 'cancelled', 'Cancelled'

    member          = models.ForeignKey(Member, on_delete=models.CASCADE,
                                        related_name='installment_plans')
    invoice         = models.ForeignKey(Invoice, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='installment_plans')
    description     = models.CharField(max_length=200)
    total_amount    = models.DecimalField(max_digits=10, decimal_places=2)
    down_payment    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    num_installments= models.PositiveIntegerField(default=3)
    installment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date      = models.DateField()
    status          = models.CharField(max_length=12, choices=Status.choices,
                                       default=Status.ACTIVE)
    notes           = models.TextField(blank=True)
    created_by      = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'installment_plans'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.member.get_full_name()} — {self.description} ({self.num_installments} installments)"

    @property
    def amount_paid(self):
        return sum(i.amount for i in self.installments.filter(status='paid'))

    @property
    def amount_remaining(self):
        return float(self.total_amount) - float(self.amount_paid)

    @property
    def progress_pct(self):
        if not self.total_amount:
            return 0
        return min(int(float(self.amount_paid) / float(self.total_amount) * 100), 100)

    def get_status_color(self):
        return {'active':'blue','completed':'green','defaulted':'red','cancelled':'gray'}.get(self.status,'gray')


class Installment(models.Model):

    class Status(models.TextChoices):
        PENDING   = 'pending',   'Pending'
        PAID      = 'paid',      'Paid'
        OVERDUE   = 'overdue',   'Overdue'
        WAIVED    = 'waived',    'Waived'

    plan        = models.ForeignKey(InstallmentPlan, on_delete=models.CASCADE,
                                    related_name='installments')
    number      = models.PositiveIntegerField()
    due_date    = models.DateField()
    amount      = models.DecimalField(max_digits=10, decimal_places=2)
    paid_date   = models.DateField(null=True, blank=True)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status      = models.CharField(max_length=10, choices=Status.choices,
                                   default=Status.PENDING)
    payment     = models.ForeignKey(Payment, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='installments')
    notes       = models.TextField(blank=True)

    class Meta:
        db_table = 'installments'
        ordering = ['number']

    def __str__(self):
        return f"Installment #{self.number} — {self.plan}"

    @property
    def is_overdue(self):
        return self.status == 'pending' and self.due_date < timezone.now().date()

    def get_status_color(self):
        return {'pending':'orange','paid':'green','overdue':'red','waived':'gray'}.get(self.status,'gray')


# ── Refund ─────────────────────────────────────────────────
class Refund(models.Model):

    class Reason(models.TextChoices):
        CANCELLATION  = 'cancellation',  'Membership Cancellation'
        DUPLICATE     = 'duplicate',     'Duplicate Payment'
        OVERCHARGE    = 'overcharge',    'Overcharge'
        SERVICE_ISSUE = 'service_issue', 'Service Issue'
        OTHER         = 'other',         'Other'

    class Status(models.TextChoices):
        PENDING   = 'pending',   'Pending Approval'
        APPROVED  = 'approved',  'Approved'
        PROCESSED = 'processed', 'Processed'
        REJECTED  = 'rejected',  'Rejected'

    payment         = models.ForeignKey(Payment, on_delete=models.CASCADE,
                                        related_name='refunds')
    member          = models.ForeignKey(Member, on_delete=models.CASCADE,
                                        related_name='refunds')
    reason          = models.CharField(max_length=20, choices=Reason.choices)
    amount          = models.DecimalField(max_digits=10, decimal_places=2)
    status          = models.CharField(max_length=12, choices=Status.choices,
                                       default=Status.PENDING)
    notes           = models.TextField(blank=True)
    requested_by    = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='requested_refunds')
    approved_by     = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='approved_refunds')
    requested_at    = models.DateTimeField(auto_now_add=True)
    processed_at    = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'refunds'
        ordering = ['-requested_at']

    def __str__(self):
        return f"Refund {self.amount} EGP — {self.member.get_full_name()}"

    def get_status_color(self):
        return {'pending':'orange','approved':'blue','processed':'green','rejected':'red'}.get(self.status,'gray')


# ── Cash Register ──────────────────────────────────────────
class CashRegister(models.Model):

    class Status(models.TextChoices):
        OPEN   = 'open',   'Open'
        CLOSED = 'closed', 'Closed'

    date            = models.DateField(default=timezone.now, unique=True)
    status          = models.CharField(max_length=8, choices=Status.choices,
                                       default=Status.OPEN)
    opening_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    closing_balance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_cash_in   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cash_out  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    opened_by       = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='opened_registers')
    closed_by       = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='closed_registers')
    opened_at       = models.DateTimeField(auto_now_add=True)
    closed_at       = models.DateTimeField(null=True, blank=True)
    notes           = models.TextField(blank=True)

    class Meta:
        db_table = 'cash_registers'
        ordering = ['-date']

    def __str__(self):
        return f"Cash Register {self.date} ({self.status})"

    @property
    def total_revenue(self):
        return Payment.objects.filter(
            payment_date=self.date,
            status='completed'
        ).aggregate(t=models.Sum('net_amount'))['t'] or 0

    @property
    def cash_revenue(self):
        return Payment.objects.filter(
            payment_date=self.date,
            status='completed',
            method='cash'
        ).aggregate(t=models.Sum('net_amount'))['t'] or 0

    @property
    def expected_closing(self):
        return float(self.opening_balance) + float(self.cash_revenue)
