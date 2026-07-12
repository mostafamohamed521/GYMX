from django.contrib import admin
from .models import (ProductCategory, Brand, Supplier, Warehouse, Product, Stock,
                      StockMovement, DamagedItem, PurchaseOrder, PurchaseOrderItem,
                      Equipment, EquipmentMaintenance)

admin.site.register(ProductCategory)
admin.site.register(Brand)
admin.site.register(Supplier)
admin.site.register(Warehouse)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display  = ['name','sku','category','brand','cost_price','sale_price']
    list_filter   = ['category','brand','is_active']
    search_fields = ['name','sku','barcode']


admin.site.register(Stock)
admin.site.register(StockMovement)
admin.site.register(DamagedItem)


class POItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['po_number','supplier','status','total_amount','order_date']
    list_filter  = ['status']
    inlines      = [POItemInline]


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['name','category','brand','status','location']
    list_filter  = ['status','category']
    search_fields= ['name','serial_number']


admin.site.register(EquipmentMaintenance)
