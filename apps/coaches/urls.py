from django.urls import path
from . import views

app_name = 'coaches'

urlpatterns = [
    path('',                             views.coach_list,         name='list'),
    path('add/',                         views.coach_add,          name='add'),
    path('<int:pk>/',                    views.coach_detail,       name='detail'),
    path('<int:pk>/edit/',               views.coach_edit,         name='edit'),
    path('<int:pk>/schedule/',           views.coach_schedule,     name='schedule'),
    path('<int:pk>/calendar/',           views.coach_calendar,     name='calendar'),
    path('<int:pk>/members/',            views.assigned_members,   name='members'),
    path('<int:pk>/classes/',            views.assigned_classes,   name='classes'),
    path('<int:pk>/attendance/',         views.coach_attendance,   name='attendance'),
    path('<int:pk>/salary/',             views.coach_salary,       name='salary'),
    path('<int:pk>/commissions/',        views.coach_commissions,  name='commissions'),
    path('<int:pk>/performance/',        views.coach_performance,  name='performance'),
    path('<int:pk>/certificates/',       views.coach_certificates, name='certificates'),
    path('<int:pk>/notes/',              views.coach_notes,        name='notes'),
    path('<int:pk>/availability/',       views.coach_availability, name='availability'),
]
