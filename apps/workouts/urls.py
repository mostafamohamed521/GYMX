from django.urls import path
from . import views

app_name = 'workouts'

urlpatterns = [
    # Plans
    path('',                              views.workout_plans,        name='plans'),
    path('plans/new/',                    views.plan_new,             name='plan_new'),
    path('plans/<int:pk>/',              views.plan_detail,          name='plan_detail'),

    # Templates
    path('templates/',                    views.workout_templates,    name='templates'),
    path('templates/new/',               views.template_new,         name='template_new'),

    # Exercise Library
    path('exercises/',                    views.exercise_library,     name='exercises'),
    path('exercises/categories/',        views.exercise_categories,  name='categories'),
    path('exercises/<int:pk>/',          views.exercise_detail,      name='exercise_detail'),
    path('exercises/new/',               views.exercise_new,         name='exercise_new'),

    # Builder
    path('builder/',                      views.workout_builder,      name='builder'),
    path('assign/',                       views.assign_workout,       name='assign'),

    # Progress & History
    path('progress/<int:member_pk>/',    views.workout_progress,     name='progress'),
    path('history/<int:member_pk>/',     views.workout_history,      name='history'),

    # PT Sessions
    path('pt-sessions/',                  views.pt_sessions,          name='pt_sessions'),
    path('pt-sessions/new/',             views.pt_session_new,       name='pt_session_new'),

    # Statistics
    path('statistics/',                   views.workout_statistics,   name='statistics'),

    # AJAX
    path('ajax/complete-session/<int:pk>/', views.ajax_complete_session, name='ajax_complete'),
]
