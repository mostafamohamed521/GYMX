from django.contrib import admin
from django.utils.html import format_html
from .models import AttendanceRecord, AttendanceSession, AttendanceSettings


@admin.register(AttendanceSettings)
class AttendanceSettingsAdmin(admin.ModelAdmin):
    list_display = ['gym_open_time','gym_close_time','max_session_hours','late_threshold_min','require_membership']


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display  = ['date','is_open','total_visitors','opened_at']
    list_filter   = ['is_open','date']
    ordering      = ['-date']
    def total_visitors(self,obj): return obj.total_visitors
    total_visitors.short_description='Visitors'


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display  = ['member','date','check_in_fmt','check_out_fmt','duration_fmt','status_badge','check_in_method']
    list_filter   = ['status','check_in_method','date']
    search_fields = ['member__first_name','member__last_name','member__member_id']
    ordering      = ['-date','-check_in']
    date_hierarchy = 'date'

    def check_in_fmt(self,obj): return obj.check_in.strftime('%H:%M') if obj.check_in else '—'
    check_in_fmt.short_description='In'
    def check_out_fmt(self,obj): return obj.check_out.strftime('%H:%M') if obj.check_out else '—'
    check_out_fmt.short_description='Out'
    def duration_fmt(self,obj): return obj.duration_display
    duration_fmt.short_description='Duration'
    def status_badge(self,obj):
        colors={'present':('#ECFDF5','#065F46'),'late':('#FFFBEB','#92400E'),'left':('#EFF6FF','#1E40AF')}
        bg,fg=colors.get(obj.status,('#F8FAFC','#475569'))
        return format_html('<span style="background:{};color:{};padding:3px 10px;border-radius:999px;font-size:11px;font-weight:600;">{}</span>',bg,fg,obj.get_status_display())
    status_badge.short_description='Status'
