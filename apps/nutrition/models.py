from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from apps.accounts.models import User
from apps.members.models import Member
from apps.coaches.models import Coach


class FoodCategory(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    icon        = models.CharField(max_length=50, default='fa-apple-whole')
    color       = models.CharField(max_length=7, default='#10B981')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'food_categories'
        ordering = ['name']
        verbose_name_plural = 'Food Categories'

    def __str__(self):
        return self.name


class Food(models.Model):
    class Unit(models.TextChoices):
        GRAM    = 'g',   'Grams'
        KG      = 'kg',  'Kilograms'
        ML      = 'ml',  'Milliliters'
        CUP     = 'cup', 'Cup'
        PIECE   = 'pcs', 'Piece'
        TBSP    = 'tbsp','Tablespoon'
        TSP     = 'tsp', 'Teaspoon'

    name            = models.CharField(max_length=200)
    category        = models.ForeignKey(FoodCategory, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='foods')
    serving_size    = models.FloatField(default=100)
    serving_unit    = models.CharField(max_length=5, choices=Unit.choices, default=Unit.GRAM)
    calories        = models.FloatField(default=0, validators=[MinValueValidator(0)])
    protein         = models.FloatField(default=0)
    carbs           = models.FloatField(default=0)
    fat             = models.FloatField(default=0)
    fiber           = models.FloatField(default=0)
    sugar           = models.FloatField(default=0)
    sodium          = models.FloatField(default=0)
    is_active       = models.BooleanField(default=True)
    created_by      = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'foods'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.calories} kcal per {self.serving_size}{self.serving_unit})"


class Ingredient(models.Model):
    name        = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ingredients'
        ordering = ['name']

    def __str__(self):
        return self.name


class Meal(models.Model):
    class MealType(models.TextChoices):
        BREAKFAST = 'breakfast', 'Breakfast'
        LUNCH     = 'lunch',     'Lunch'
        DINNER    = 'dinner',    'Dinner'
        SNACK     = 'snack',     'Snack'
        PRE_WO    = 'pre_workout',  'Pre-Workout'
        POST_WO   = 'post_workout', 'Post-Workout'

    name            = models.CharField(max_length=200)
    meal_type       = models.CharField(max_length=15, choices=MealType.choices,
                                       default=MealType.BREAKFAST)
    description     = models.TextField(blank=True)
    instructions    = models.TextField(blank=True)
    prep_time_min   = models.PositiveIntegerField(default=10)
    total_calories  = models.FloatField(default=0)
    total_protein   = models.FloatField(default=0)
    total_carbs     = models.FloatField(default=0)
    total_fat       = models.FloatField(default=0)
    is_active       = models.BooleanField(default=True)
    created_by      = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'meals'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.meal_type})"

    def get_type_color(self):
        return {
            'breakfast':'orange','lunch':'blue','dinner':'purple',
            'snack':'green','pre_workout':'red','post_workout':'teal',
        }.get(self.meal_type,'gray')


class MealFood(models.Model):
    meal        = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='foods')
    food        = models.ForeignKey(Food, on_delete=models.CASCADE)
    quantity    = models.FloatField(default=1)
    notes       = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'meal_foods'


class NutritionPlan(models.Model):
    class Goal(models.TextChoices):
        WEIGHT_LOSS  = 'weight_loss',  'Weight Loss'
        MUSCLE_GAIN  = 'muscle_gain',  'Muscle Gain'
        MAINTENANCE  = 'maintenance',  'Maintenance'
        ENDURANCE    = 'endurance',    'Endurance'
        HEALTH       = 'health',       'General Health'

    class Status(models.TextChoices):
        ACTIVE    = 'active',    'Active'
        PAUSED    = 'paused',    'Paused'
        COMPLETED = 'completed', 'Completed'

    member          = models.ForeignKey(Member, on_delete=models.CASCADE,
                                        related_name='nutrition_plans')
    coach           = models.ForeignKey(Coach, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='nutrition_plans')
    name            = models.CharField(max_length=200)
    goal            = models.CharField(max_length=15, choices=Goal.choices,
                                       default=Goal.HEALTH)
    status          = models.CharField(max_length=12, choices=Status.choices,
                                       default=Status.ACTIVE)
    daily_calories  = models.PositiveIntegerField(default=2000)
    daily_protein   = models.FloatField(default=150)
    daily_carbs     = models.FloatField(default=250)
    daily_fat       = models.FloatField(default=65)
    daily_water_ml  = models.PositiveIntegerField(default=2500)
    start_date      = models.DateField()
    end_date        = models.DateField(null=True, blank=True)
    notes           = models.TextField(blank=True)
    created_by      = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'nutrition_plans'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.member.get_full_name()} — {self.name}"

    def get_status_color(self):
        return {'active':'green','paused':'orange','completed':'blue'}.get(self.status,'gray')

    def get_goal_color(self):
        return {
            'weight_loss':'orange','muscle_gain':'blue','maintenance':'green',
            'endurance':'purple','health':'teal',
        }.get(self.goal,'gray')


class MealPlan(models.Model):
    class DayOfWeek(models.IntegerChoices):
        MONDAY    = 0, 'Monday'
        TUESDAY   = 1, 'Tuesday'
        WEDNESDAY = 2, 'Wednesday'
        THURSDAY  = 3, 'Thursday'
        FRIDAY    = 4, 'Friday'
        SATURDAY  = 5, 'Saturday'
        SUNDAY    = 6, 'Sunday'

    nutrition_plan  = models.ForeignKey(NutritionPlan, on_delete=models.CASCADE,
                                        related_name='meal_plans')
    day_of_week     = models.IntegerField(choices=DayOfWeek.choices)
    meal            = models.ForeignKey(Meal, on_delete=models.CASCADE)
    meal_order      = models.PositiveIntegerField(default=1)
    notes           = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'meal_plans'
        ordering = ['day_of_week', 'meal_order']

    def __str__(self):
        return f"{self.nutrition_plan} — {self.get_day_of_week_display()} — {self.meal.name}"


class WaterIntake(models.Model):
    member      = models.ForeignKey(Member, on_delete=models.CASCADE,
                                    related_name='water_logs')
    date        = models.DateField(default=timezone.now)
    amount_ml   = models.PositiveIntegerField()
    logged_at   = models.DateTimeField(auto_now_add=True)
    notes       = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'water_intake'
        ordering = ['-date', '-logged_at']

    def __str__(self):
        return f"{self.member.get_full_name()} — {self.amount_ml}ml on {self.date}"


class Supplement(models.Model):
    class Frequency(models.TextChoices):
        DAILY   = 'daily',   'Daily'
        WEEKLY  = 'weekly',  'Weekly'
        AS_NEED = 'as_needed','As Needed'
        PRE_WO  = 'pre_wo',  'Pre-Workout'
        POST_WO = 'post_wo', 'Post-Workout'

    member      = models.ForeignKey(Member, on_delete=models.CASCADE,
                                    related_name='supplements')
    name        = models.CharField(max_length=200)
    brand       = models.CharField(max_length=100, blank=True)
    dosage      = models.CharField(max_length=100)
    frequency   = models.CharField(max_length=10, choices=Frequency.choices,
                                   default=Frequency.DAILY)
    start_date  = models.DateField()
    end_date    = models.DateField(null=True, blank=True)
    notes       = models.TextField(blank=True)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'supplements'
        ordering = ['-is_active', 'name']

    def __str__(self):
        return f"{self.member.get_full_name()} — {self.name}"


class NutritionLog(models.Model):
    member          = models.ForeignKey(Member, on_delete=models.CASCADE,
                                        related_name='nutrition_logs')
    date            = models.DateField(default=timezone.now)
    calories_target = models.PositiveIntegerField(default=2000)
    calories_actual = models.PositiveIntegerField(default=0)
    protein_actual  = models.FloatField(default=0)
    carbs_actual    = models.FloatField(default=0)
    fat_actual      = models.FloatField(default=0)
    water_ml        = models.PositiveIntegerField(default=0)
    notes           = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'nutrition_logs'
        ordering = ['-date']
        unique_together = ['member', 'date']

    def __str__(self):
        return f"{self.member.get_full_name()} — {self.date}"

    @property
    def calorie_pct(self):
        if not self.calories_target:
            return 0
        return min(int(self.calories_actual / self.calories_target * 100), 100)
