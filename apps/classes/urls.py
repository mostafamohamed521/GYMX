from django.urls import path
from . import views

app_name = 'classes'

urlpatterns = [
    path('',                              views.classes_list,         name='list'),
    path('add/',                          views.class_add,            name='add'),
    path('<int:pk>/',                     views.class_detail,         name='detail'),
    path('<int:pk>/edit/',                views.class_edit,           name='edit'),
    path('schedule/',                     views.weekly_schedule,      name='schedule'),
    path('calendar/',                     views.monthly_calendar,     name='calendar'),
    path('sessions/<int:pk>/book/',       views.booking,              name='booking'),
    path('sessions/<int:pk>/waitlist/',   views.waiting_list,         name='waitlist'),
    path('sessions/<int:pk>/attendance/', views.class_attendance,     name='attendance'),
    path('capacity/',                     views.capacity_management,  name='capacity'),
    path('statistics/',                   views.class_statistics,     name='statistics'),
    path('sessions/<int:pk>/cancel-booking/<int:member_pk>/', views.cancel_booking, name='cancel_booking'),
]
