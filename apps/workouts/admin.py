from django.contrib import admin
from django.utils.html import format_html
from .models import Exercise, ExerciseCategory, WorkoutTemplate, WorkoutPlan, WorkoutSession, SessionExercise, PTSession


@admin.register(ExerciseCategory)
class ExerciseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name','icon','color']


class SessionExerciseInline(admin.TabularInline):
    model  = SessionExercise
    extra  = 0
    fields = ['exercise','sets','reps','weight_kg','rest_sec']


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display  = ['name','muscle_group','equipment','difficulty_badge','calories_per_min','is_active']
    list_filter   = ['muscle_group','difficulty','equipment','is_active']
    search_fields = ['name']
    ordering      = ['name']

    def difficulty_badge(self,obj):
        c={'beginner':('#ECFDF5','#065F46'),'intermediate':('#FFFBEB','#92400E'),'advanced':('#FEF2F2','#991B1B')}
        bg,fg=c.get(obj.difficulty,('#F8FAFC','#475569'))
        return format_html('<span style="background:{};color:{};padding:3px 10px;border-radius:999px;font-size:11px;font-weight:600;">{}</span>',bg,fg,obj.get_difficulty_display())
    difficulty_badge.short_description='Difficulty'


@admin.register(WorkoutTemplate)
class WorkoutTemplateAdmin(admin.ModelAdmin):
    list_display = ['name','goal','difficulty','duration_weeks','days_per_week','is_public']
    list_filter  = ['goal','difficulty','is_public']


@admin.register(WorkoutPlan)
class WorkoutPlanAdmin(admin.ModelAdmin):
    list_display = ['member','name','goal','status','coach','start_date']
    list_filter  = ['status','goal']
    search_fields= ['member__first_name','member__last_name','name']
    ordering     = ['-created_at']


@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = ['plan','name','scheduled_date','status','duration_min','calories_burned']
    list_filter  = ['status']
    ordering     = ['-scheduled_date']
    inlines      = [SessionExerciseInline]


@admin.register(PTSession)
class PTSessionAdmin(admin.ModelAdmin):
    list_display = ['member','coach','date','start_time','end_time','status','rating']
    list_filter  = ['status','date']
    ordering     = ['-date']
