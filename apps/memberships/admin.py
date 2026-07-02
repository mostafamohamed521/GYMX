from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from .models import (
    MembershipCategory, MembershipPlan, MemberSubscription,
    Discount, Coupon, Offer, FamilyMembership, FamilyMember,
    CorporateMembership, CorporateEmployee,
)


@admin.register(MembershipCategory)
class MembershipCategoryAdmin(admin.ModelAdmin):
    list_display  = ['name', 'color_preview', 'icon', 'is_active', 'sort_order']
    list_filter   = ['is_active']
    search_fields = ['name']
    ordering      = ['sort_order', 'name']

    def color_preview(self, obj):
        return format_html(
            '<span style="display:inline-block;width:20px;height:20px;background:{};border-radius:4px;vertical-align:middle;"></span> {}',
            obj.color, obj.color
        )
    color_preview.short_description = 'Color'


class MemberSubscriptionInline(admin.TabularInline):
    model    = MemberSubscription
    fk_name  = 'plan'
    extra    = 0
    fields   = ['member', 'status', 'start_date', 'end_date', 'final_price', 'payment_status']
    readonly_fields = ['member', 'status', 'start_date', 'end_date']
    show_change_link = True


@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    list_display  = ['name', 'plan_type', 'billing_cycle', 'price_display',
                     'active_subs', 'is_active', 'is_featured']
    list_filter   = ['plan_type', 'billing_cycle', 'is_active', 'is_featured', 'category']
    search_fields = ['name', 'description']
    ordering      = ['sort_order', 'price']
    readonly_fields = ['created_at', 'updated_at']
    inlines       = [MemberSubscriptionInline]

    fieldsets = (
        ('Basic',    {'fields': ('category', 'name', 'plan_type', 'billing_cycle',
                                  'duration_days', 'price', 'setup_fee', 'description')}),
        ('Features', {'fields': ('features',)}),
        ('Rules',    {'fields': ('max_freeze_days', 'max_members')}),
        ('Settings', {'fields': ('is_active', 'is_featured', 'is_public', 'sort_order')}),
        ('Meta',     {'fields': ('created_by', 'created_at', 'updated_at'),
                      'classes': ('collapse',)}),
    )

    def price_display(self, obj):
        return format_html('<strong style="color:#3B82F6;">{} EGP</strong>', obj.price)
    price_display.short_description = 'Price'

    def active_subs(self, obj):
        count = obj.subscriptions.filter(status='active').count()
        color = '#10B981' if count > 0 else '#94A3B8'
        return format_html('<span style="color:{};">{}</span>', color, count)
    active_subs.short_description = 'Active Subs'


@admin.register(MemberSubscription)
class MemberSubscriptionAdmin(admin.ModelAdmin):
    list_display  = ['member', 'plan', 'status_badge', 'payment_badge',
                     'start_date', 'end_date', 'final_price_display', 'days_left']
    list_filter   = ['status', 'payment_status', 'plan', 'auto_renew']
    search_fields = ['member__first_name', 'member__last_name',
                     'member__member_id', 'plan__name']
    ordering      = ['-start_date']
    readonly_fields = ['created_at', 'updated_at', 'activation_date']
    date_hierarchy = 'start_date'

    fieldsets = (
        ('Core',     {'fields': ('member', 'plan', 'status', 'payment_status')}),
        ('Dates',    {'fields': ('start_date', 'end_date', 'activation_date', 'cancelled_at')}),
        ('Pricing',  {'fields': ('original_price', 'discount_amount', 'final_price',
                                  'amount_paid', 'coupon', 'discount')}),
        ('Freeze',   {'fields': ('freeze_start', 'freeze_end', 'freeze_days_used'),
                      'classes': ('collapse',)}),
        ('Upgrade',  {'fields': ('previous_plan', 'upgrade_type'),
                      'classes': ('collapse',)}),
        ('Options',  {'fields': ('auto_renew', 'parent_subscription', 'notes')}),
        ('Meta',     {'fields': ('created_by', 'created_at', 'updated_at'),
                      'classes': ('collapse',)}),
    )

    def status_badge(self, obj):
        colors = {
            'active':    ('#ECFDF5', '#065F46'),
            'expired':   ('#FEF2F2', '#991B1B'),
            'frozen':    ('#EFF6FF', '#1E40AF'),
            'cancelled': ('#F8FAFC', '#475569'),
            'pending':   ('#FFFBEB', '#92400E'),
            'trial':     ('#F0F9FF', '#0369A1'),
            'grace':     ('#FFFBEB', '#92400E'),
        }
        bg, fg = colors.get(obj.status, ('#F8FAFC', '#475569'))
        return format_html(
            '<span style="background:{};color:{};padding:3px 10px;border-radius:999px;font-size:11px;font-weight:600;">{}</span>',
            bg, fg, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def payment_badge(self, obj):
        colors = {
            'paid':     ('#ECFDF5', '#065F46'),
            'unpaid':   ('#FEF2F2', '#991B1B'),
            'partial':  ('#FFFBEB', '#92400E'),
            'refunded': ('#F0F9FF', '#0369A1'),
            'waived':   ('#F8FAFC', '#475569'),
        }
        bg, fg = colors.get(obj.payment_status, ('#F8FAFC', '#475569'))
        return format_html(
            '<span style="background:{};color:{};padding:3px 10px;border-radius:999px;font-size:11px;font-weight:600;">{}</span>',
            bg, fg, obj.get_payment_status_display()
        )
    payment_badge.short_description = 'Payment'

    def final_price_display(self, obj):
        return format_html('<strong style="color:#3B82F6;">{} EGP</strong>',
                           obj.final_price)
    final_price_display.short_description = 'Amount'

    def days_left(self, obj):
        d = obj.days_remaining
        color = '#10B981' if d > 14 else '#F59E0B' if d > 7 else '#EF4444'
        return format_html('<span style="color:{};">{}</span>', color, d)
    days_left.short_description = 'Days Left'


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display  = ['name', 'discount_type', 'value_display', 'times_used',
                     'usage_limit', 'is_active', 'valid_until']
    list_filter   = ['discount_type', 'is_active']
    search_fields = ['name']
    filter_horizontal = ['applicable_plans']

    def value_display(self, obj):
        suffix = '%' if obj.discount_type == 'percentage' else ' EGP'
        return format_html('<strong>{}{}</strong>', obj.value, suffix)
    value_display.short_description = 'Value'


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display  = ['code', 'discount', 'member', 'times_used',
                     'is_single_use', 'is_active', 'valid_until']
    list_filter   = ['is_active', 'is_single_use']
    search_fields = ['code', 'member__first_name', 'member__last_name']
    ordering      = ['-created_at']


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display  = ['name', 'offer_type', 'discount', 'valid_from',
                     'valid_until', 'is_active', 'is_featured']
    list_filter   = ['offer_type', 'is_active', 'is_featured']
    search_fields = ['name', 'description']
    filter_horizontal = ['applicable_plans']


class FamilyMemberInline(admin.TabularInline):
    model  = FamilyMember
    extra  = 0
    fields = ['member', 'relationship', 'joined_at']
    readonly_fields = ['joined_at']


@admin.register(FamilyMembership)
class FamilyMembershipAdmin(admin.ModelAdmin):
    list_display  = ['name', 'primary_member', 'plan', 'member_count', 'max_members']
    search_fields = ['name', 'primary_member__first_name', 'primary_member__last_name']
    inlines       = [FamilyMemberInline]

    def member_count(self, obj):
        return obj.member_count
    member_count.short_description = 'Members'


class CorporateEmployeeInline(admin.TabularInline):
    model  = CorporateEmployee
    extra  = 0
    fields = ['member', 'employee_id', 'department', 'enrolled_at']
    readonly_fields = ['enrolled_at']


@admin.register(CorporateMembership)
class CorporateMembershipAdmin(admin.ModelAdmin):
    list_display  = ['company_name', 'contact_person', 'plan', 'enrolled_count',
                     'max_employees', 'contract_end', 'is_active']
    list_filter   = ['is_active', 'plan']
    search_fields = ['company_name', 'contact_person', 'company_email']
    inlines       = [CorporateEmployeeInline]

    def enrolled_count(self, obj):
        return obj.enrolled_count
    enrolled_count.short_description = 'Enrolled'
