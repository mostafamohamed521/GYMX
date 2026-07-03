from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # Dashboard
    path('',                        views.attendance_dashboard,  name='dashboard'),

    # Live operations
    path('checkin/',                views.live_checkin,          name='live_checkin'),
    path('checkout/',               views.live_checkout,         name='live_checkout'),
    path('qr-scanner/',            views.qr_scanner,            name='qr_scanner'),
    path('barcode-scanner/',       views.barcode_scanner,       name='barcode_scanner'),
    path('face-recognition/',      views.face_recognition,      name='face_recognition'),

    # Records
    path('today/',                  views.today_attendance,      name='today'),
    path('calendar/',               views.attendance_calendar,   name='calendar'),
    path('history/',                views.attendance_history,    name='history'),
    path('member/<int:pk>/',        views.member_attendance,     name='member'),

    # Reports & analytics
    path('reports/',                views.attendance_reports,    name='reports'),
    path('late/',                   views.late_members,          name='late'),
    path('absent/',                 views.absent_members,        name='absent'),
    path('statistics/',             views.attendance_statistics, name='statistics'),

    # AJAX
    path('ajax/checkin/',           views.ajax_checkin,          name='ajax_checkin'),
    path('ajax/checkout/',          views.ajax_checkout,         name='ajax_checkout'),
    path('ajax/live-count/',        views.ajax_live_count,       name='ajax_live_count'),
]
