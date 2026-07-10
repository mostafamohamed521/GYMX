from django.contrib import admin
from .models import ClassCategory, GymClass, ClassSchedule, ClassSession, ClassBooking, ClassAttendance


@admin.register(ClassCategory)
class ClassCategoryAdmin(admin.ModelAdmin):
    list_display = ['name','icon','color']


class ClassScheduleInline(admin.TabularInline):
    model = ClassSchedule
    extra = 1


@admin.register(GymClass)
class GymClassAdmin(admin.ModelAdmin):
    list_display  = ['name','category','coach','difficulty','max_capacity','status']
    list_filter   = ['status','difficulty','category']
    search_fields = ['name']
    inlines       = [ClassScheduleInline]


class ClassBookingInline(admin.TabularInline):
    model = ClassBooking
    extra = 0


@admin.register(ClassSession)
class ClassSessionAdmin(admin.ModelAdmin):
    list_display = ['gym_class','date','start_time','status','booked_count']
    list_filter  = ['status','date']
    ordering     = ['-date']
    inlines      = [ClassBookingInline]

    def booked_count(self, obj): return obj.booked_count


@admin.register(ClassBooking)
class ClassBookingAdmin(admin.ModelAdmin):
    list_display = ['member','session','status','booked_at']
    list_filter  = ['status']
    ordering     = ['-booked_at']
