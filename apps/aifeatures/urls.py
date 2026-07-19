from django.urls import path
from . import views

app_name = 'aifeatures'

urlpatterns = [
    path('',                              views.ai_dashboard,          name='dashboard'),
    path('workout-generator/',            views.workout_generator,    name='workout_generator'),
    path('nutrition-advisor/',            views.nutrition_advisor,    name='nutrition_advisor'),
    path('chat/',                         views.chat_assistant,       name='chat'),
    path('chat/send/',                    views.chat_send,            name='chat_send'),
    path('recommendations/',              views.smart_recommendations, name='recommendations'),
    path('churn-prediction/',             views.churn_prediction,     name='churn'),
    path('revenue-forecast/',             views.revenue_forecast,     name='forecast'),
    path('attendance-prediction/',        views.attendance_prediction, name='attendance_prediction'),
]
