from django.contrib import admin
from .models import ChatConversation, ChatMessage, GeneratedWorkoutPlan, GeneratedNutritionAdvice

admin.site.register(ChatConversation)
admin.site.register(ChatMessage)
admin.site.register(GeneratedWorkoutPlan)
admin.site.register(GeneratedNutritionAdvice)
