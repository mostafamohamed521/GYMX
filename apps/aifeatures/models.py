from django.db import models
from django.utils import timezone
from apps.accounts.models import User
from apps.members.models import Member


class ChatConversation(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_conversations')
    title       = models.CharField(max_length=150, default='New Conversation')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_chat_conversations'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class ChatMessage(models.Model):
    class Sender(models.TextChoices):
        USER = 'user', 'User'
        AI   = 'ai',   'AI Assistant'

    conversation= models.ForeignKey(ChatConversation, on_delete=models.CASCADE, related_name='messages')
    sender      = models.CharField(max_length=5, choices=Sender.choices, default=Sender.USER)
    message     = models.TextField()
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_chat_messages'
        ordering = ['created_at']


class GeneratedWorkoutPlan(models.Model):
    class Goal(models.TextChoices):
        WEIGHT_LOSS  = 'weight_loss',  'Weight Loss'
        MUSCLE_GAIN  = 'muscle_gain',  'Muscle Gain'
        ENDURANCE    = 'endurance',    'Endurance'
        GENERAL_FIT  = 'general_fit',  'General Fitness'

    class Level(models.TextChoices):
        BEGINNER     = 'beginner',     'Beginner'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED     = 'advanced',     'Advanced'

    member      = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='ai_workout_plans')
    goal        = models.CharField(max_length=12, choices=Goal.choices, default=Goal.GENERAL_FIT)
    level       = models.CharField(max_length=12, choices=Level.choices, default=Level.BEGINNER)
    days_per_week = models.PositiveIntegerField(default=3)
    generated_plan = models.JSONField(default=dict)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_generated_workout_plans'
        ordering = ['-created_at']

    def __str__(self):
        return f"AI Plan — {self.member.get_full_name()} — {self.get_goal_display()}"


class GeneratedNutritionAdvice(models.Model):
    member      = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='ai_nutrition_advice')
    weight_kg   = models.FloatField()
    height_cm   = models.FloatField()
    age         = models.PositiveIntegerField()
    gender      = models.CharField(max_length=10, choices=[('male','Male'),('female','Female')])
    activity_level = models.CharField(max_length=20, default='moderate')
    goal        = models.CharField(max_length=20, default='maintain')
    bmr         = models.FloatField(default=0)
    tdee        = models.FloatField(default=0)
    recommended_calories = models.FloatField(default=0)
    protein_g   = models.FloatField(default=0)
    carbs_g     = models.FloatField(default=0)
    fat_g       = models.FloatField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_nutrition_advice'
        ordering = ['-created_at']

    def __str__(self):
        return f"Nutrition Advice — {self.member.get_full_name()}"
