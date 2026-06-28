from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Member, EmergencyContact, MedicalInformation,
    BodyMeasurement, BodyComposition, ProgressPhoto,
    MemberDocument, MemberNote, MemberGoal, MemberTimeline,
)


class EmergencyContactInline(admin.TabularInline):
    model   = EmergencyContact
    extra   = 0
    fields  = ['name','relationship','phone','is_primary']


class MedicalInfoInline(admin.StackedInline):
    model  = MedicalInformation
    extra  = 0
    fields = ['blood_type','height_cm','weight_kg','chronic_conditions','allergies']


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display   = ['member_id','full_name','email','phone','status_badge','fitness_level','assigned_coach','join_date']
    list_filter    = ['status','fitness_level','gender','blood_type']
    search_fields  = ['first_name','last_name','email','phone','member_id','national_id']
    ordering       = ['-created_at']
    readonly_fields= ['member_id','created_at','updated_at','qr_code','barcode_image']
    inlines        = [EmergencyContactInline, MedicalInfoInline]

    fieldsets = (
        ('Identity',  {'fields':('member_id','first_name','last_name','profile_image')}),
        ('Contact',   {'fields':('email','phone','phone_secondary','address')}),
        ('Personal',  {'fields':('gender','birth_date','nationality','national_id','occupation','blood_type')}),
        ('Fitness',   {'fields':('fitness_level','status','join_date')}),
        ('Freeze',    {'fields':('freeze_start','freeze_end','freeze_reason'),'classes':('collapse',)}),
        ('Blacklist', {'fields':('blacklist_reason',),'classes':('collapse',)}),
        ('Archive',   {'fields':('archived_at','archive_reason'),'classes':('collapse',)}),
        ('Staff',     {'fields':('assigned_coach','assigned_nutritionist','registered_by')}),
        ('QR/Barcode',{'fields':('qr_code','barcode_image'),'classes':('collapse',)}),
        ('Notes',     {'fields':('notes',)}),
        ('Timestamps',{'fields':('created_at','updated_at'),'classes':('collapse',)}),
    )

    def full_name(self, obj):
        return obj.get_full_name()
    full_name.short_description = 'Name'

    def status_badge(self, obj):
        colors = {
            'active':    ('#ECFDF5','#065F46'),
            'inactive':  ('#F8FAFC','#475569'),
            'frozen':    ('#EFF6FF','#1E40AF'),
            'archived':  ('#FFFBEB','#92400E'),
            'blacklist': ('#FEF2F2','#991B1B'),
            'pending':   ('#FFFBEB','#92400E'),
        }
        bg, fg = colors.get(obj.status, ('#F8FAFC','#475569'))
        return format_html(
            '<span style="background:{};color:{};padding:3px 10px;border-radius:999px;font-size:11px;font-weight:600;">{}</span>',
            bg, fg, obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(MemberNote)
class MemberNoteAdmin(admin.ModelAdmin):
    list_display  = ['member','title','priority','is_pinned','created_by','created_at']
    list_filter   = ['priority','is_pinned']
    search_fields = ['member__first_name','member__last_name','title','body']
    ordering      = ['-created_at']


@admin.register(MemberGoal)
class MemberGoalAdmin(admin.ModelAdmin):
    list_display  = ['member','title','goal_type','status','progress_pct','target_date']
    list_filter   = ['goal_type','status']
    search_fields = ['member__first_name','member__last_name','title']
    ordering      = ['-created_at']

    def progress_pct(self, obj):
        pct = obj.progress_pct
        color = '#10B981' if pct >= 75 else '#3B82F6' if pct >= 50 else '#F59E0B'
        return format_html(
            '<div style="background:#F1F5F9;border-radius:999px;height:8px;width:80px;overflow:hidden;">'
            '<div style="background:{};height:100%;width:{}%;border-radius:999px;"></div></div>'
            '<span style="font-size:11px;color:#64748B;margin-left:6px;">{}%</span>',
            color, pct, pct
        )
    progress_pct.short_description = 'Progress'


@admin.register(BodyMeasurement)
class BodyMeasurementAdmin(admin.ModelAdmin):
    list_display  = ['member','date','weight_kg','height_cm','bmi_display','recorded_by']
    list_filter   = ['date']
    search_fields = ['member__first_name','member__last_name']
    ordering      = ['-date']

    def bmi_display(self, obj):
        bmi = obj.bmi
        if not bmi:
            return '—'
        color = '#10B981' if 18.5 <= bmi < 25 else '#F59E0B' if 25 <= bmi < 30 else '#EF4444'
        return format_html('<span style="color:{};">{}</span>', color, bmi)
    bmi_display.short_description = 'BMI'


@admin.register(MemberTimeline)
class MemberTimelineAdmin(admin.ModelAdmin):
    list_display  = ['member','event_type','title','date','created_by']
    list_filter   = ['event_type','date']
    search_fields = ['member__first_name','member__last_name','title']
    ordering      = ['-date']


admin.site.register(EmergencyContact)
admin.site.register(MedicalInformation)
admin.site.register(BodyComposition)
admin.site.register(ProgressPhoto)
admin.site.register(MemberDocument)
