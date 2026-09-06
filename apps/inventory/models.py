from django.db import models
from django.utils import timezone
from apps.accounts.models import User


class ProductCategory(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    icon        = models.CharField(max_length=50, default='fa-box')
    color       = models.CharField(max_length=7, default='#C80036')

    class Meta:
        db_table = 'product_categories'
        ordering = ['name']
        verbose_name_plural = 'Product Categories'

    def __str__(self):
        return self.name


class Brand(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    logo        = models.ImageField(upload_to='brands/', null=True, blank=True)
    website     = models.URLField(blank=True)

    class Meta:
        db_table = 'brands'
        ordering = ['name']

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name            = models.CharField(max_length=200)
    contact_person  = models.CharField(max_length=100, blank=True)
    phone           = models.CharField(max_length=20, blank=True)
    email           = models.EmailField(blank=True)
    address         = models.TextField(blank=True)
    notes           = models.TextField(blank=True)
    is_active       = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'suppliers'
        ordering = ['name']

    def __str__(self):
        return self.name


class Warehouse(models.Model):
    name        = models.CharField(max_length=100)
    location    = models.CharField(max_length=200, blank=True)
    is_active   = models.BooleanField(default=True)

    class Meta:
        db_table = 'warehouses'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    class Unit(models.TextChoices):
        PIECE = 'pcs', 'Piece'
        BOX   = 'box', 'Box'
        KG    = 'kg',  'Kilogram'
        LITER = 'l',   'Liter'

    name        = models.CharField(max_length=200)
    sku         = models.CharField(max_length=50, unique=True, blank=True)
    barcode     = models.CharField(max_length=50, blank=True)
    category    = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='products')
    brand       = models.ForeignKey(Brand, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='products')
    unit        = models.CharField(max_length=5, choices=Unit.choices, default=Unit.PIECE)
    cost_price  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale_price  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reorder_level = models.PositiveIntegerField(default=10)
    description = models.TextField(blank=True)
    image       = models.ImageField(upload_to='products/', null=True, blank=True)
    is_active   = models.BooleanField(default=True)
    is_sellable = models.BooleanField(default=True, help_text='Show in POS')
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'products'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.sku:
            last = Product.objects.count() + 1
            self.sku = f"SKU-{str(last).zfill(5)}"
        super().save(*args, **kwargs)

    @property
    def total_stock(self):
        return self.stock_entries.aggregate(t=models.Sum('quantity'))['t'] or 0

    @property
    def is_low_stock(self):
        return self.total_stock <= self.reorder_level

    @property
    def profit_margin(self):
        if self.cost_price:
            return round((float(self.sale_price) - float(self.cost_price)) / float(self.cost_price) * 100, 1)
        return 0


class Stock(models.Model):
    product     = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_entries')
    warehouse   = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='stock_entries')
    quantity    = models.IntegerField(default=0)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stock'
        unique_together = ['product', 'warehouse']

    def __str__(self):
        return f"{self.product.name} @ {self.warehouse.name}: {self.quantity}"


class StockMovement(models.Model):
    class MoveType(models.TextChoices):
        IN       = 'in',       'Stock In'
        OUT      = 'out',      'Stock Out'
        TRANSFER = 'transfer', 'Transfer'
        DAMAGE   = 'damage',   'Damaged'
        ADJUST   = 'adjust',   'Adjustment'

    product      = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements')
    warehouse    = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='movements')
    move_type    = models.CharField(max_length=10, choices=MoveType.choices, default=MoveType.IN)
    quantity     = models.IntegerField()
    reference    = models.CharField(max_length=100, blank=True)
    notes        = models.TextField(blank=True)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stock_movements'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_move_type_display()} — {self.product.name} ({self.quantity})"

    def get_type_color(self):
        return {'in':'green','out':'blue','transfer':'purple','damage':'red','adjust':'orange'}.get(self.move_type,'gray')


class DamagedItem(models.Model):
    product     = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='damaged_records')
    warehouse   = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True)
    quantity    = models.PositiveIntegerField()
    reason      = models.TextField(blank=True)
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'damaged_items'
        ordering = ['-reported_at']

    def __str__(self):
        return f"{self.product.name} — {self.quantity} damaged"


class PurchaseOrder(models.Model):
    class Status(models.TextChoices):
        DRAFT     = 'draft',     'Draft'
        ORDERED   = 'ordered',   'Ordered'
        RECEIVED  = 'received',  'Received'
        CANCELLED = 'cancelled', 'Cancelled'

    po_number   = models.CharField(max_length=30, unique=True, editable=False)
    supplier    = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchase_orders')
    warehouse   = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True)
    status      = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    order_date  = models.DateField(default=timezone.now)
    expected_date = models.DateField(null=True, blank=True)
    total_amount= models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes       = models.TextField(blank=True)
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'purchase_orders'
        ordering = ['-order_date']

    def __str__(self):
        return self.po_number

    def save(self, *args, **kwargs):
        if not self.po_number:
            last = PurchaseOrder.objects.count() + 1
            self.po_number = f"PO-{timezone.now().strftime('%Y%m')}-{str(last).zfill(4)}"
        super().save(*args, **kwargs)

    def get_status_color(self):
        return {'draft':'gray','ordered':'blue','received':'green','cancelled':'red'}.get(self.status,'gray')


class PurchaseOrderItem(models.Model):
    po          = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product     = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity    = models.PositiveIntegerField()
    unit_price  = models.DecimalField(max_digits=10, decimal_places=2)
    total       = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = 'purchase_order_items'

    def save(self, *args, **kwargs):
        self.total = float(self.quantity) * float(self.unit_price)
        super().save(*args, **kwargs)


class Equipment(models.Model):
    class Status(models.TextChoices):
        OPERATIONAL = 'operational', 'Operational'
        MAINTENANCE = 'maintenance', 'Under Maintenance'
        BROKEN      = 'broken',      'Broken'
        RETIRED     = 'retired',     'Retired'

    name            = models.CharField(max_length=200)
    category        = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='equipment')
    brand           = models.ForeignKey(Brand, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='equipment')
    serial_number   = models.CharField(max_length=100, blank=True)
    purchase_date   = models.DateField(null=True, blank=True)
    purchase_price  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    warranty_until  = models.DateField(null=True, blank=True)
    location        = models.CharField(max_length=100, blank=True)
    status          = models.CharField(max_length=12, choices=Status.choices,
                                       default=Status.OPERATIONAL)
    image           = models.ImageField(upload_to='equipment/', null=True, blank=True)
    notes           = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'equipment'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_status_color(self):
        return {'operational':'green','maintenance':'orange','broken':'red','retired':'gray'}.get(self.status,'gray')

    @property
    def is_under_warranty(self):
        return self.warranty_until and self.warranty_until >= timezone.now().date()

    @property
    def warranty_expiring_soon(self):
        if self.warranty_until:
            return 0 < (self.warranty_until - timezone.now().date()).days <= 30
        return False


class EquipmentMaintenance(models.Model):
    class MaintenanceType(models.TextChoices):
        ROUTINE  = 'routine',  'Routine Check'
        REPAIR   = 'repair',   'Repair'
        CLEANING = 'cleaning', 'Cleaning'
        UPGRADE  = 'upgrade',  'Upgrade'

    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    equipment       = models.ForeignKey(Equipment, on_delete=models.CASCADE,
                                        related_name='maintenance_records')
    maintenance_type= models.CharField(max_length=10, choices=MaintenanceType.choices,
                                       default=MaintenanceType.ROUTINE)
    status          = models.CharField(max_length=10, choices=Status.choices,
                                       default=Status.SCHEDULED)
    scheduled_date  = models.DateField()
    completed_date  = models.DateField(null=True, blank=True)
    cost            = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    technician      = models.CharField(max_length=100, blank=True)
    notes           = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'equipment_maintenance'
        ordering = ['-scheduled_date']

    def __str__(self):
        return f"{self.equipment.name} — {self.get_maintenance_type_display()}"

    def get_status_color(self):
        return {'scheduled':'blue','completed':'green','cancelled':'gray'}.get(self.status,'gray')
