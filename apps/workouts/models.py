from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.accounts.models import User
from apps.members.models import Member
from apps.coaches.models import Coach


class ExerciseCategory(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon        = models.CharField(max_length=50, default='fa-dumbbell')
    color       = models.CharField(max_length=7, default='#C80036')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'exercise_categories'
        ordering = ['name']
        verbose_name_plural = 'Exercise Categories'

    def __str__(self):
        return self.name


class Exercise(models.Model):
    class Difficulty(models.TextChoices):
        BEGINNER     = 'beginner',     'Beginner'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED     = 'advanced',     'Advanced'

    class MuscleGroup(models.TextChoices):
        CHEST       = 'chest',        'Chest'
        BACK        = 'back',         'Back'
        SHOULDERS   = 'shoulders',    'Shoulders'
        BICEPS      = 'biceps',       'Biceps'
        TRICEPS     = 'triceps',      'Triceps'
        FOREARMS    = 'forearms',     'Forearms'
        ABS         = 'abs',          'Abs / Core'
        GLUTES      = 'glutes',       'Glutes'
        QUADS       = 'quads',        'Quadriceps'
        HAMSTRINGS  = 'hamstrings',   'Hamstrings'
        CALVES      = 'calves',       'Calves'
        FULL_BODY   = 'full_body',    'Full Body'
        CARDIO      = 'cardio',       'Cardio'

    class Equipment(models.TextChoices):
        BARBELL     = 'barbell',      'Barbell'
        DUMBBELL    = 'dumbbell',     'Dumbbell'
        MACHINE     = 'machine',      'Machine'
        CABLE       = 'cable',        'Cable'
        BODYWEIGHT  = 'bodyweight',   'Bodyweight'
        KETTLEBELL  = 'kettlebell',   'Kettlebell'
        RESISTANCE  = 'resistance',   'Resistance Band'
        CARDIO_EQ   = 'cardio_eq',    'Cardio Equipment'
        NONE        = 'none',         'No Equipment'

    name            = models.CharField(max_length=200)
    category        = models.ForeignKey(ExerciseCategory, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='exercises')
    muscle_group    = models.CharField(max_length=15, choices=MuscleGroup.choices,
                                       default=MuscleGroup.CHEST)
    secondary_muscles = models.CharField(max_length=200, blank=True)
    equipment       = models.CharField(max_length=12, choices=Equipment.choices,
                                       default=Equipment.DUMBBELL)
    difficulty      = models.CharField(max_length=14, choices=Difficulty.choices,
                                       default=Difficulty.BEGINNER)
    description     = models.TextField(blank=True)
    instructions    = models.TextField(blank=True)
    tips            = models.TextField(blank=True)
    video_url       = models.URLField(blank=True)
    image           = models.ImageField(upload_to='exercises/', null=True, blank=True)
    calories_per_min= models.FloatField(default=5.0)
    is_active       = models.BooleanField(default=True)
    created_by      = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'exercises'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_difficulty_color(self):
        return {'beginner':'green','intermediate':'orange','advanced':'red'}.get(self.difficulty,'gray')

    def get_muscle_icon(self):
        return {
            'chest':'fa-person','back':'fa-person','shoulders':'fa-person',
            'biceps':'fa-hand-rock','triceps':'fa-hand-rock','abs':'fa-person',
            'quads':'fa-person-walking','hamstrings':'fa-person-walking',
            'calves':'fa-person-walking','glutes':'fa-person-walking',
            'full_body':'fa-person-running','cardio':'fa-heart-pulse',
        }.get(self.muscle_group, 'fa-dumbbell')


class WorkoutTemplate(models.Model):
    class Goal(models.TextChoices):
        WEIGHT_LOSS  = 'weight_loss',  'Weight Loss'
        MUSCLE_GAIN  = 'muscle_gain',  'Muscle Gain'
        STRENGTH     = 'strength',     'Strength'
        ENDURANCE    = 'endurance',    'Endurance'
        FLEXIBILITY  = 'flexibility',  'Flexibility'
        GENERAL      = 'general',      'General Fitness'

    name            = models.CharField(max_length=200)
    description     = models.TextField(blank=True)
    goal            = models.CharField(max_length=15, choices=Goal.choices,
                                       default=Goal.GENERAL)
    difficulty      = models.CharField(max_length=14,
                                       choices=Exercise.Difficulty.choices,
                                       default=Exercise.Difficulty.BEGINNER)
    duration_weeks  = models.PositiveIntegerField(default=4)
    days_per_week   = models.PositiveIntegerField(default=3)
    session_duration= models.PositiveIntegerField(default=60, help_text='Minutes')
    is_public       = models.BooleanField(default=True)
    created_by      = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'workout_templates'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_goal_color(self):
        return {
            'weight_loss':'orange','muscle_gain':'blue','strength':'red',
            'endurance':'green','flexibility':'purple','general':'gray',
        }.get(self.goal,'gray')


class WorkoutPlan(models.Model):
    class Status(models.TextChoices):
        ACTIVE    = 'active',    'Active'
        PAUSED    = 'paused',    'Paused'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    member          = models.ForeignKey(Member, on_delete=models.CASCADE,
                                        related_name='workout_plans')
    coach           = models.ForeignKey(Coach, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='member_plans')
    template        = models.ForeignKey(WorkoutTemplate, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='instances')
    name            = models.CharField(max_length=200)
    goal            = models.CharField(max_length=15, choices=WorkoutTemplate.Goal.choices,
                                       default=WorkoutTemplate.Goal.GENERAL)
    status          = models.CharField(max_length=12, choices=Status.choices,
                                       default=Status.ACTIVE)
    start_date      = models.DateField()
    end_date        = models.DateField(null=True, blank=True)
    notes           = models.TextField(blank=True)
    created_by      = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'workout_plans'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.member.get_full_name()} — {self.name}"

    def get_status_color(self):
        return {'active':'green','paused':'orange','completed':'blue','cancelled':'gray'}.get(self.status,'gray')

    @property
    def progress_pct(self):
        total = self.sessions.count()
        done  = self.sessions.filter(status='completed').count()
        return round(done / max(total, 1) * 100)


class WorkoutSession(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        COMPLETED = 'completed', 'Completed'
        SKIPPED   = 'skipped',   'Skipped'
        CANCELLED = 'cancelled', 'Cancelled'

    plan            = models.ForeignKey(WorkoutPlan, on_delete=models.CASCADE,
                                        related_name='sessions')
    name            = models.CharField(max_length=200, default='Workout Session')
    scheduled_date  = models.DateField()
    completed_date  = models.DateField(null=True, blank=True)
    status          = models.CharField(max_length=12, choices=Status.choices,
                                       default=Status.SCHEDULED)
    duration_min    = models.PositiveIntegerField(null=True, blank=True)
    calories_burned = models.PositiveIntegerField(null=True, blank=True)
    notes           = models.TextField(blank=True)
    coach_feedback  = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'workout_sessions'
        ordering = ['scheduled_date']

    def __str__(self):
        return f"{self.plan.member.get_full_name()} — {self.name} ({self.scheduled_date})"

    def get_status_color(self):
        return {'scheduled':'blue','completed':'green','skipped':'orange','cancelled':'gray'}.get(self.status,'gray')


class SessionExercise(models.Model):
    session     = models.ForeignKey(WorkoutSession, on_delete=models.CASCADE,
                                    related_name='exercises')
    exercise    = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    order       = models.PositiveIntegerField(default=1)
    sets        = models.PositiveIntegerField(default=3)
    reps        = models.CharField(max_length=20, default='10')
    weight_kg   = models.FloatField(null=True, blank=True)
    duration_sec= models.PositiveIntegerField(null=True, blank=True)
    rest_sec    = models.PositiveIntegerField(default=60)
    notes       = models.TextField(blank=True)
    # Actual performance
    actual_sets = models.PositiveIntegerField(null=True, blank=True)
    actual_reps = models.CharField(max_length=20, blank=True)
    actual_weight = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'session_exercises'
        ordering = ['order']


class PTSession(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        NO_SHOW   = 'no_show',   'No Show'

    member          = models.ForeignKey(Member, on_delete=models.CASCADE,
                                        related_name='pt_sessions')
    coach           = models.ForeignKey(Coach, on_delete=models.CASCADE,
                                        related_name='pt_sessions')
    workout_plan    = models.ForeignKey(WorkoutPlan, on_delete=models.SET_NULL,
                                        null=True, blank=True)
    date            = models.DateField()
    start_time      = models.TimeField()
    end_time        = models.TimeField()
    status          = models.CharField(max_length=12, choices=Status.choices,
                                       default=Status.SCHEDULED)
    notes           = models.TextField(blank=True)
    feedback        = models.TextField(blank=True)
    rating          = models.PositiveIntegerField(null=True, blank=True,
                                                  validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pt_sessions'
        ordering = ['-date', '-start_time']

    def __str__(self):
        return f"PT: {self.member.get_full_name()} with {self.coach.get_full_name()} — {self.date}"

    def get_status_color(self):
        return {'scheduled':'blue','completed':'green','cancelled':'gray','no_show':'red'}.get(self.status,'gray')
