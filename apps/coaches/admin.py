from django.contrib import admin
from django.utils.html import format_html
from .models import Coach, CoachSpecialization, CoachCertificate, CoachNote, CoachAvailability, CoachSchedule, CoachAttendance, CoachSalary, CoachCommission


@admin.register(CoachSpecialization)
class CoachSpecializationAdmin(admin.ModelAdmin):
    list_display = ['name','icon','color']
    search_fields = ['name']


class CertificateInline(admin.TabularInline):
    model = CoachCertificate
    extra = 1
    fields = ['title','issued_by','issue_date','expiry_date']


@admin.register(Coach)
class CoachAdmin(admin.ModelAdmin):
    list_display  = ['photo','get_full_name','status_badge','employment_type','experience_years','base_salary','rating']
    list_filter   = ['status','employment_type']
    search_fields = ['first_name','last_name','email','phone']
    ordering      = ['first_name']
    filter_horizontal = ['specializations']
    inlines       = [CertificateInline]
    readonly_fields = ['created_at','updated_at']

    def photo(self, obj):
        if obj.profile_image:
            return format_html('<img src="{}" style="width:32px;height:32px;border-radius:50%;object-fit:cover;" />', obj.profile_image.url)
        return format_html('<div style="width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,#3B82F6,#0EA5E9);display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:12px;">{}</div>', obj.get_initials())
    photo.short_description = ''

    def status_badge(self, obj):
        colors = {'active':('#ECFDF5','#065F46'),'inactive':('#F8FAFC','#475569'),'on_leave':('#FFFBEB','#92400E'),'terminated':('#FEF2F2','#991B1B')}
        bg, fg = colors.get(obj.status, ('#F8FAFC','#475569'))
        return format_html('<span style="background:{};color:{};padding:3px 10px;border-radius:999px;font-size:11px;font-weight:600;">{}</span>', bg, fg, obj.get_status_display())
    status_badge.short_description = 'Status'


@admin.register(CoachAttendance)
class CoachAttendanceAdmin(admin.ModelAdmin):
    list_display = ['coach','date','status','check_in','check_out']
    list_filter  = ['status','date']
    ordering     = ['-date']


@admin.register(CoachSalary)
class CoachSalaryAdmin(admin.ModelAdmin):
    list_display = ['coach','month','base_salary','net_salary','status']
    list_filter  = ['status']
    ordering     = ['-month']


@admin.register(CoachCommission)
class CoachCommissionAdmin(admin.ModelAdmin):
    list_display = ['coach','member','description','amount','date','is_paid']
    list_filter  = ['is_paid']
    ordering     = ['-date']
