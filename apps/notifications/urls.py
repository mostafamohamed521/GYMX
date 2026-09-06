from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('',                              views.notification_center,  name='center'),
    path('<int:pk>/read/',                views.mark_read,            name='mark_read'),
    path('mark-all-read/',                views.mark_all_read,        name='mark_all_read'),

    path('email-templates/',              views.email_templates,      name='email_templates'),
    path('email-templates/new/',          views.email_template_new,   name='email_template_new'),
    path('sms-templates/',                views.sms_templates,        name='sms_templates'),
    path('sms-templates/new/',            views.sms_template_new,     name='sms_template_new'),

    path('push/',                         views.push_notifications,   name='push'),
    path('push/new/',                     views.push_new,             name='push_new'),

    path('announcements/',                views.announcement_center,  name='announcements'),
    path('announcements/new/',            views.announcement_new,     name='announcement_new'),

    path('birthdays/',                    views.birthday_messages,    name='birthdays'),
    path('birthdays/send/<int:pk>/',      views.birthday_send,        name='birthday_send'),

    path('expiry-alerts/',                views.expiry_alerts,        name='expiry_alerts'),
    path('payment-reminders/',            views.payment_reminders,    name='payment_reminders'),
    path('payment-reminders/send/<str:kind>/<int:pk>/', views.payment_reminder_send, name='payment_reminder_send'),

    path('scheduled/',                    views.scheduled_messages,   name='scheduled'),
    path('scheduled/new/',                views.scheduled_new,        name='scheduled_new'),
]
