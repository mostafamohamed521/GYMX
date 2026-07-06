from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import Payment, Invoice, InvoiceItem, Receipt, InstallmentPlan, Installment, Refund, CashRegister


class InvoiceItemInline(admin.TabularInline):
    model  = InvoiceItem
    extra  = 1
    fields = ['description','quantity','unit_price','total']
    readonly_fields = ['total']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display  = ['invoice_number','member','status_badge','issue_date','due_date','total_fmt','amount_due_fmt']
    list_filter   = ['status']
    search_fields = ['invoice_number','member__first_name','member__last_name']
    ordering      = ['-issue_date']
    inlines       = [InvoiceItemInline]
    readonly_fields = ['invoice_number','created_at','updated_at']

    def status_badge(self, obj):
        colors = {'paid':('#ECFDF5','#065F46'),'overdue':('#FEF2F2','#991B1B'),'draft':('#F8FAFC','#475569'),'sent':('#EFF6FF','#1E40AF'),'partial':('#FFFBEB','#92400E'),'cancelled':('#F8FAFC','#475569')}
        bg,fg = colors.get(obj.status,('#F8FAFC','#475569'))
        return format_html('<span style="background:{};color:{};padding:3px 10px;border-radius:999px;font-size:11px;font-weight:600;">{}</span>',bg,fg,obj.get_status_display())
    status_badge.short_description='Status'

    def total_fmt(self, obj): return f"{obj.total} EGP"
    total_fmt.short_description='Total'

    def amount_due_fmt(self, obj):
        due = obj.amount_due
        color = '#EF4444' if due > 0 else '#10B981'
        return format_html('<span style="color:{};font-weight:700;">{} EGP</span>', color, due)
    amount_due_fmt.short_description='Due'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display  = ['member','payment_date','payment_type','method','amount_fmt','status_badge','received_by']
    list_filter   = ['status','method','payment_type','payment_date']
    search_fields = ['member__first_name','member__last_name','member__member_id','reference']
    ordering      = ['-payment_date','-created_at']
    date_hierarchy = 'payment_date'
    readonly_fields = ['created_at','net_amount']

    def amount_fmt(self,obj):
        return format_html('<strong style="color:#10B981;">{} EGP</strong>',obj.net_amount)
    amount_fmt.short_description='Amount'

    def status_badge(self,obj):
        colors={'completed':('#ECFDF5','#065F46'),'pending':('#FFFBEB','#92400E'),'failed':('#FEF2F2','#991B1B'),'refunded':('#F5F3FF','#6D28D9'),'cancelled':('#F8FAFC','#475569')}
        bg,fg=colors.get(obj.status,('#F8FAFC','#475569'))
        return format_html('<span style="background:{};color:{};padding:3px 10px;border-radius:999px;font-size:11px;font-weight:600;">{}</span>',bg,fg,obj.get_status_display())
    status_badge.short_description='Status'


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ['receipt_number','payment','issued_at','issued_by']
    search_fields = ['receipt_number','payment__member__first_name','payment__member__last_name']
    ordering = ['-issued_at']
    readonly_fields = ['receipt_number','issued_at']


class InstallmentInline(admin.TabularInline):
    model  = Installment
    extra  = 0
    fields = ['number','due_date','amount','status','paid_date']
    readonly_fields = ['number']


@admin.register(InstallmentPlan)
class InstallmentPlanAdmin(admin.ModelAdmin):
    list_display  = ['member','description','total_amount','num_installments','status','created_at']
    list_filter   = ['status']
    search_fields = ['member__first_name','member__last_name','description']
    ordering      = ['-created_at']
    inlines       = [InstallmentInline]


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display  = ['member','payment','reason','amount','status','requested_at']
    list_filter   = ['status','reason']
    search_fields = ['member__first_name','member__last_name']
    ordering      = ['-requested_at']


@admin.register(CashRegister)
class CashRegisterAdmin(admin.ModelAdmin):
    list_display  = ['date','status','opening_balance','closing_balance','opened_by','closed_by']
    list_filter   = ['status']
    ordering      = ['-date']
    readonly_fields = ['opened_at','closed_at']
