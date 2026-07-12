from django.db import models
from django.utils import timezone
from apps.accounts.models import User
from apps.members.models import Member
from apps.inventory.models import Product, Warehouse, Stock, StockMovement


class Discount(models.Model):
    class DiscountType(models.TextChoices):
        PERCENT = 'percent', 'Percentage'
        FIXED   = 'fixed',   'Fixed Amount'

    code        = models.CharField(max_length=30, unique=True)
    description = models.CharField(max_length=200, blank=True)
    discount_type = models.CharField(max_length=8, choices=DiscountType.choices,
                                     default=DiscountType.PERCENT)
    value       = models.DecimalField(max_digits=10, decimal_places=2)
    is_active   = models.BooleanField(default=True)
    valid_from  = models.DateField(default=timezone.now)
    valid_until = models.DateField(null=True, blank=True)
    max_uses    = models.PositiveIntegerField(null=True, blank=True)
    used_count  = models.PositiveIntegerField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pos_discounts'
        ordering = ['-created_at']

    def __str__(self):
        return self.code

    @property
    def is_valid(self):
        today = timezone.now().date()
        if not self.is_active:
            return False
        if self.valid_until and today > self.valid_until:
            return False
        if self.max_uses and self.used_count >= self.max_uses:
            return False
        return True

    def calculate_discount(self, subtotal):
        if self.discount_type == 'percent':
            return float(subtotal) * float(self.value) / 100
        return min(float(self.value), float(subtotal))


class GiftCard(models.Model):
    class Status(models.TextChoices):
        ACTIVE   = 'active',   'Active'
        REDEEMED = 'redeemed', 'Fully Redeemed'
        EXPIRED  = 'expired',  'Expired'
        DISABLED = 'disabled', 'Disabled'

    code        = models.CharField(max_length=30, unique=True, editable=False)
    initial_amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance     = models.DecimalField(max_digits=10, decimal_places=2)
    status      = models.CharField(max_length=10, choices=Status.choices,
                                   default=Status.ACTIVE)
    purchased_by= models.ForeignKey(Member, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='gift_cards_purchased')
    issued_to   = models.CharField(max_length=200, blank=True)
    issue_date  = models.DateField(default=timezone.now)
    expiry_date = models.DateField(null=True, blank=True)
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pos_gift_cards'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} ({self.balance} EGP)"

    def save(self, *args, **kwargs):
        if not self.code:
            import random, string
            self.code = 'GC-' + ''.join(random.choices(string.ascii_uppercase+string.digits, k=10))
        if self.balance is None:
            self.balance = self.initial_amount
        super().save(*args, **kwargs)

    def get_status_color(self):
        return {'active':'green','redeemed':'gray','expired':'red','disabled':'orange'}.get(self.status,'gray')


class Sale(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH    = 'cash',    'Cash'
        CARD    = 'card',    'Card'
        WALLET  = 'wallet',  'Digital Wallet'
        GIFT_CARD = 'gift_card', 'Gift Card'
        MEMBER_ACCOUNT = 'member_account', 'Member Account'

    class Status(models.TextChoices):
        COMPLETED = 'completed', 'Completed'
        REFUNDED  = 'refunded',  'Refunded'
        PARTIAL_REFUND = 'partial_refund', 'Partially Refunded'
        VOIDED    = 'voided',    'Voided'

    invoice_number  = models.CharField(max_length=30, unique=True, editable=False)
    member          = models.ForeignKey(Member, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='pos_sales')
    warehouse       = models.ForeignKey(Warehouse, on_delete=models.SET_NULL,
                                        null=True, blank=True)
    cashier         = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='sales_made')
    subtotal        = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_code   = models.ForeignKey(Discount, on_delete=models.SET_NULL,
                                        null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total           = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method  = models.CharField(max_length=15, choices=PaymentMethod.choices,
                                       default=PaymentMethod.CASH)
    gift_card       = models.ForeignKey(GiftCard, on_delete=models.SET_NULL,
                                        null=True, blank=True)
    status          = models.CharField(max_length=15, choices=Status.choices,
                                       default=Status.COMPLETED)
    amount_received = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    change_due       = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes           = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pos_sales'
        ordering = ['-created_at']

    def __str__(self):
        return self.invoice_number

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            prefix = timezone.now().strftime('%Y%m%d')
            last = Sale.objects.filter(invoice_number__startswith=f'POS-{prefix}').count() + 1
            self.invoice_number = f"POS-{prefix}-{str(last).zfill(4)}"
        super().save(*args, **kwargs)

    def get_status_color(self):
        return {'completed':'green','refunded':'red','partial_refund':'orange','voided':'gray'}.get(self.status,'gray')

    def get_method_icon(self):
        return {
            'cash':'fa-money-bill-wave','card':'fa-credit-card','wallet':'fa-wallet',
            'gift_card':'fa-gift','member_account':'fa-user',
        }.get(self.payment_method,'fa-coins')


class SaleItem(models.Model):
    sale        = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product     = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name= models.CharField(max_length=200)
    quantity    = models.PositiveIntegerField(default=1)
    unit_price  = models.DecimalField(max_digits=10, decimal_places=2)
    total       = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_returned = models.BooleanField(default=False)
    returned_qty= models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'pos_sale_items'

    def save(self, *args, **kwargs):
        self.total = float(self.quantity) * float(self.unit_price)
        if self.product and not self.product_name:
            self.product_name = self.product.name
        super().save(*args, **kwargs)


class Return(models.Model):
    class Reason(models.TextChoices):
        DEFECTIVE  = 'defective',  'Defective Product'
        WRONG_ITEM = 'wrong_item', 'Wrong Item'
        UNWANTED   = 'unwanted',   'No Longer Wanted'
        OTHER      = 'other',      'Other'

    sale        = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='returns')
    sale_item   = models.ForeignKey(SaleItem, on_delete=models.CASCADE, related_name='return_records')
    quantity    = models.PositiveIntegerField(default=1)
    reason      = models.CharField(max_length=12, choices=Reason.choices, default=Reason.OTHER)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes       = models.TextField(blank=True)
    processed_by= models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pos_returns'
        ordering = ['-created_at']

    def __str__(self):
        return f"Return — {self.sale.invoice_number} — {self.quantity}x"
