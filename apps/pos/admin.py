from django.contrib import admin
from .models import Discount, GiftCard, Sale, SaleItem, Return


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ['code','discount_type','value','used_count','is_active']
    list_filter  = ['discount_type','is_active']


@admin.register(GiftCard)
class GiftCardAdmin(admin.ModelAdmin):
    list_display = ['code','initial_amount','balance','status']
    list_filter  = ['status']


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display  = ['invoice_number','member','total','payment_method','status','created_at']
    list_filter   = ['status','payment_method']
    search_fields = ['invoice_number']
    inlines       = [SaleItemInline]


@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = ['sale','quantity','reason','refund_amount','created_at']
    list_filter  = ['reason']
