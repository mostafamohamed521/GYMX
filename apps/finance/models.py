from django.db import models
from django.utils import timezone
from apps.accounts.models import User


class Account(models.Model):
    """Chart of Accounts — simplified."""
    class AccountType(models.TextChoices):
        ASSET     = 'asset',     'Asset'
        LIABILITY = 'liability', 'Liability'
        EQUITY    = 'equity',    'Equity'
        INCOME    = 'income',    'Income'
        EXPENSE   = 'expense',   'Expense'

    code        = models.CharField(max_length=10, unique=True)
    name        = models.CharField(max_length=150)
    account_type= models.CharField(max_length=10, choices=AccountType.choices)
    description = models.CharField(max_length=255, blank=True)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'finance_accounts'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} — {self.name}"

    def get_type_color(self):
        return {'asset':'blue','liability':'red','equity':'purple','income':'green','expense':'orange'}.get(self.account_type,'gray')

    @property
    def balance(self):
        debit  = self.journal_lines.aggregate(t=models.Sum('debit'))['t'] or 0
        credit = self.journal_lines.aggregate(t=models.Sum('credit'))['t'] or 0
        if self.account_type in ('asset', 'expense'):
            return float(debit) - float(credit)
        return float(credit) - float(debit)


class JournalEntry(models.Model):
    class Status(models.TextChoices):
        DRAFT   = 'draft',   'Draft'
        POSTED  = 'posted',  'Posted'
        VOIDED  = 'voided',  'Voided'

    entry_number = models.CharField(max_length=30, unique=True, editable=False)
    date        = models.DateField(default=timezone.now)
    description = models.CharField(max_length=255)
    reference   = models.CharField(max_length=100, blank=True)
    status      = models.CharField(max_length=8, choices=Status.choices, default=Status.POSTED)
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'finance_journal_entries'
        ordering = ['-date', '-id']

    def __str__(self):
        return self.entry_number

    def save(self, *args, **kwargs):
        if not self.entry_number:
            prefix = timezone.now().strftime('%Y%m')
            last = JournalEntry.objects.filter(entry_number__startswith=f'JE-{prefix}').count() + 1
            self.entry_number = f"JE-{prefix}-{str(last).zfill(4)}"
        super().save(*args, **kwargs)

    def get_status_color(self):
        return {'draft':'gray','posted':'green','voided':'red'}.get(self.status,'gray')

    @property
    def total_debit(self):
        return self.lines.aggregate(t=models.Sum('debit'))['t'] or 0

    @property
    def total_credit(self):
        return self.lines.aggregate(t=models.Sum('credit'))['t'] or 0

    @property
    def is_balanced(self):
        return self.total_debit == self.total_credit


class JournalLine(models.Model):
    entry       = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account     = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='journal_lines')
    debit       = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit      = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes       = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'finance_journal_lines'

    def __str__(self):
        return f"{self.account.name} — Dr {self.debit} / Cr {self.credit}"


class Income(models.Model):
    class Category(models.TextChoices):
        MEMBERSHIP = 'membership', 'Membership Fees'
        POS_SALES  = 'pos_sales',  'POS Sales'
        PT_SESSION = 'pt_session', 'PT Sessions'
        OTHER      = 'other',      'Other'

    date        = models.DateField(default=timezone.now)
    category    = models.CharField(max_length=12, choices=Category.choices, default=Category.OTHER)
    description = models.CharField(max_length=255)
    amount      = models.DecimalField(max_digits=12, decimal_places=2)
    account     = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='income_records')
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'finance_income'
        ordering = ['-date']

    def __str__(self):
        return f"{self.description} — {self.amount} EGP"

    def get_category_color(self):
        return {'membership':'green','pos_sales':'blue','pt_session':'purple','other':'gray'}.get(self.category,'gray')


class Expense(models.Model):
    class Category(models.TextChoices):
        RENT       = 'rent',       'Rent'
        UTILITIES  = 'utilities',  'Utilities'
        SALARIES   = 'salaries',   'Salaries'
        MAINTENANCE= 'maintenance','Maintenance'
        SUPPLIES   = 'supplies',   'Supplies'
        MARKETING  = 'marketing',  'Marketing'
        OTHER      = 'other',      'Other'

    date        = models.DateField(default=timezone.now)
    category    = models.CharField(max_length=12, choices=Category.choices, default=Category.OTHER)
    description = models.CharField(max_length=255)
    amount      = models.DecimalField(max_digits=12, decimal_places=2)
    vendor      = models.CharField(max_length=200, blank=True)
    account     = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='expense_records')
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'finance_expense'
        ordering = ['-date']

    def __str__(self):
        return f"{self.description} — {self.amount} EGP"

    def get_category_color(self):
        return {'rent':'red','utilities':'orange','salaries':'purple','maintenance':'blue','supplies':'gray','marketing':'green','other':'gray'}.get(self.category,'gray')


class Budget(models.Model):
    class Period(models.TextChoices):
        MONTHLY   = 'monthly',   'Monthly'
        QUARTERLY = 'quarterly', 'Quarterly'
        YEARLY    = 'yearly',    'Yearly'

    name        = models.CharField(max_length=150)
    category    = models.CharField(max_length=20, help_text='Matches Expense.Category or a custom label')
    period      = models.CharField(max_length=10, choices=Period.choices, default=Period.MONTHLY)
    allocated_amount = models.DecimalField(max_digits=12, decimal_places=2)
    start_date  = models.DateField(default=timezone.now)
    end_date    = models.DateField()
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'finance_budget'
        ordering = ['-start_date']

    def __str__(self):
        return self.name

    @property
    def spent(self):
        return Expense.objects.filter(
            category=self.category, date__gte=self.start_date, date__lte=self.end_date
        ).aggregate(t=models.Sum('amount'))['t'] or 0

    @property
    def remaining(self):
        return float(self.allocated_amount) - float(self.spent)

    @property
    def usage_pct(self):
        if self.allocated_amount:
            return min(round(float(self.spent) / float(self.allocated_amount) * 100, 1), 100)
        return 0


class TaxRecord(models.Model):
    class TaxType(models.TextChoices):
        VAT       = 'vat',       'VAT'
        INCOME_TAX= 'income_tax','Income Tax'
        PAYROLL   = 'payroll',   'Payroll Tax'
        OTHER     = 'other',     'Other'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        FILED   = 'filed',   'Filed'
        PAID    = 'paid',    'Paid'

    tax_type    = models.CharField(max_length=12, choices=TaxType.choices, default=TaxType.VAT)
    period_start= models.DateField()
    period_end  = models.DateField()
    taxable_amount = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate    = models.DecimalField(max_digits=5, decimal_places=2, default=14)
    tax_due     = models.DecimalField(max_digits=12, decimal_places=2)
    status      = models.CharField(max_length=8, choices=Status.choices, default=Status.PENDING)
    filed_date  = models.DateField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'finance_tax_records'
        ordering = ['-period_end']

    def __str__(self):
        return f"{self.get_tax_type_display()} — {self.period_start} to {self.period_end}"

    def get_status_color(self):
        return {'pending':'orange','filed':'blue','paid':'green'}.get(self.status,'gray')
