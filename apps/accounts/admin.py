from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'get_full_name', 'email', 'role_badge', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff', 'gender']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone']
    ordering = ['-created_at']

    fieldsets = (
        ('Account', {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone', 'gender', 'birth_date', 'address', 'profile_image', 'bio')}),
        ('Role & Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Timestamps', {'fields': ('date_joined', 'last_login', 'last_login_ip'), 'classes': ('collapse',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )

    readonly_fields = ['date_joined', 'last_login', 'created_at', 'updated_at', 'last_login_ip']

    def role_badge(self, obj):
        colors = {
            'super_admin': '#dc3545',
            'gym_manager': '#0d6efd',
            'receptionist': '#198754',
            'coach': '#ffc107',
            'member': '#0dcaf0',
        }
        color = colors.get(obj.role, '#6c757d')
        return format_html(
            '<span style="background:{};color:white;padding:3px 8px;border-radius:4px;font-size:11px;">{}</span>',
            color, obj.get_role_display()
        )
    role_badge.short_description = 'Role'
