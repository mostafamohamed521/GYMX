from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('',                         views.dashboard,          name='dashboard'),
    path('checkin/',                 views.live_checkin,       name='live_checkin'),
    path('checkout/',                views.live_checkout,      name='live_checkout'),
    path('qr-scanner/',             views.qr_scanner,         name='qr_scanner'),
    path('barcode-scanner/',        views.barcode_scanner,    name='barcode_scanner'),
    path('face-recognition/',       views.face_recognition,   name='face_recognition'),
    path('today/',                   views.today_attendance,   name='today'),
    path('calendar/',                views.att_calendar,       name='calendar'),
    path('history/',                 views.att_history,        name='history'),
    path('member/<int:pk>/',         views.member_attendance,  name='member'),
    path('reports/',                 views.att_reports,        name='reports'),
    path('late/',                    views.late_members,       name='late'),
    path('absent/',                  views.absent_members,     name='absent'),
    path('statistics/',              views.att_statistics,     name='statistics'),
    path('ajax/checkin/',            views.ajax_checkin,       name='ajax_checkin'),
    path('ajax/checkout/',           views.ajax_checkout,      name='ajax_checkout'),
    path('ajax/live-count/',         views.ajax_live_count,    name='ajax_live_count'),
]
