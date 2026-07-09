from django.contrib import admin
from .models import Food, FoodCategory, Ingredient, Meal, MealFood, NutritionPlan, MealPlan, WaterIntake, Supplement, NutritionLog


@admin.register(FoodCategory)
class FoodCategoryAdmin(admin.ModelAdmin):
    list_display = ['name','icon','color']


@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display  = ['name','category','calories','protein','carbs','fat','is_active']
    list_filter   = ['category','is_active']
    search_fields = ['name']


class MealFoodInline(admin.TabularInline):
    model  = MealFood
    extra  = 1


@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ['name','meal_type','total_calories','total_protein','prep_time_min','is_active']
    list_filter  = ['meal_type','is_active']
    inlines      = [MealFoodInline]


@admin.register(NutritionPlan)
class NutritionPlanAdmin(admin.ModelAdmin):
    list_display  = ['member','name','goal','status','daily_calories','coach','start_date']
    list_filter   = ['status','goal']
    search_fields = ['member__first_name','member__last_name','name']
    ordering      = ['-created_at']


@admin.register(WaterIntake)
class WaterIntakeAdmin(admin.ModelAdmin):
    list_display = ['member','amount_ml','date','logged_at']
    list_filter  = ['date']
    ordering     = ['-date','-logged_at']


@admin.register(Supplement)
class SupplementAdmin(admin.ModelAdmin):
    list_display = ['member','name','brand','dosage','frequency','is_active']
    list_filter  = ['is_active','frequency']


@admin.register(NutritionLog)
class NutritionLogAdmin(admin.ModelAdmin):
    list_display = ['member','date','calories_actual','calories_target','protein_actual','water_ml']
    ordering     = ['-date']
