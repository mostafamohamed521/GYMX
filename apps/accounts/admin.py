from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, LoginHistory, Notification, ActivityLog, UserSession


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ['username', 'get_full_name', 'email', 'role_badge', 'verified_icons', 'security_icons', 'is_active', 'date_joined']
    list_filter   = ['role', 'is_active', 'is_email_verified', 'is_phone_verified', 'two_fa_enabled', 'gender']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone']
    ordering      = ['-created_at']
    readonly_fields = ['date_joined', 'last_login', 'created_at', 'updated_at', 'last_login_ip', 'failed_login_count']

    fieldsets = (
        ('Account',      {'fields': ('username', 'email', 'password')}),
        ('Personal',     {'fields': ('first_name', 'last_name', 'phone', 'gender', 'birth_date', 'address', 'profile_image', 'bio', 'emergency_contact_name', 'emergency_contact_phone')}),
        ('Role',         {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Verification', {'fields': ('is_email_verified', 'is_phone_verified', 'two_fa_enabled')}),
        ('Preferences',  {'fields': ('theme', 'language', 'notif_email', 'notif_sms', 'notif_push', 'notif_payment', 'notif_membership', 'notif_attendance')}),
        ('Security',     {'fields': ('last_login_ip', 'failed_login_count', 'locked_until'), 'classes': ('collapse',)}),
        ('Timestamps',   {'fields': ('date_joined', 'last_login', 'created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('username', 'email', 'first_name', 'last_name', 'role', 'password1', 'password2')}),
    )

    def role_badge(self, obj):
        colors = {'super_admin':'#EF4444','gym_manager':'#3B82F6','receptionist':'#10B981','coach':'#F59E0B','member':'#8B5CF6'}
        bg = {'super_admin':'#FEF2F2','gym_manager':'#EFF6FF','receptionist':'#ECFDF5','coach':'#FFFBEB','member':'#F5F3FF'}
        c = colors.get(obj.role, '#64748B')
        b = bg.get(obj.role, '#F8FAFC')
        return format_html('<span style="background:{};color:{};padding:3px 10px;border-radius:999px;font-size:11px;font-weight:600;">{}</span>', b, c, obj.get_role_display())
    role_badge.short_description = 'Role'

    def verified_icons(self, obj):
        email = '<span title="Email Verified" style="color:#10B981;">&#10003; Email</span>' if obj.is_email_verified else '<span title="Email not verified" style="color:#94A3B8;">&#10007; Email</span>'
        phone = '<span title="Phone Verified" style="color:#10B981;margin-left:6px;">&#10003; Phone</span>' if obj.is_phone_verified else '<span title="Phone not verified" style="color:#94A3B8;margin-left:6px;">&#10007; Phone</span>'
        return format_html(email + phone)
    verified_icons.short_description = 'Verified'

    def security_icons(self, obj):
        twofa = '<span title="2FA Enabled" style="color:#10B981;">&#x1F6E1; 2FA</span>' if obj.two_fa_enabled else '<span title="2FA Disabled" style="color:#94A3B8;">&#x1F6E1; 2FA</span>'
        return format_html(twofa)
    security_icons.short_description = 'Security'


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display  = ['user', 'status_badge', 'ip_address', 'browser', 'os', 'created_at']
    list_filter   = ['status', 'created_at']
    search_fields = ['user__username', 'ip_address', 'user_agent']
    readonly_fields = ['user', 'status', 'ip_address', 'user_agent', 'created_at']
    ordering = ['-created_at']

    def status_badge(self, obj):
        colors = {'success': ('#ECFDF5','#10B981'), 'failed': ('#FEF2F2','#EF4444'), 'logout': ('#F8FAFC','#64748B'), 'locked': ('#FFFBEB','#F59E0B')}
        bg, fg = colors.get(obj.status, ('#F8FAFC','#64748B'))
        return format_html('<span style="background:{};color:{};padding:3px 10px;border-radius:999px;font-size:11px;font-weight:600;">{}</span>', bg, fg, obj.get_status_display())
    status_badge.short_description = 'Status'

    def browser(self, obj): return obj.browser
    def os(self, obj): return obj.os


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ['user', 'type', 'title', 'is_read', 'created_at']
    list_filter   = ['type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    ordering = ['-created_at']


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display  = ['user', 'action', 'description', 'ip_address', 'created_at']
    list_filter   = ['action', 'created_at']
    search_fields = ['user__username', 'description', 'ip_address']
    readonly_fields = ['user', 'action', 'description', 'ip_address', 'extra_data', 'created_at']
    ordering = ['-created_at']


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display  = ['user', 'ip_address', 'browser', 'os', 'is_active', 'last_active']
    list_filter   = ['is_active', 'created_at']
    search_fields = ['user__username', 'ip_address']
    readonly_fields = ['session_key', 'created_at', 'last_active']
    ordering = ['-last_active']

    def browser(self, obj): return obj.browser
    def os(self, obj): return obj.os
