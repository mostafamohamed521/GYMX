from django.urls import path
from . import views

app_name = 'gymsettings'

urlpatterns = [
    path('',                              views.general_settings,     name='general'),
    path('gym-info/',                     views.gym_information,      name='gym_info'),
    path('business-hours/',               views.business_hours,       name='business_hours'),
    path('holidays/',                     views.holidays,             name='holidays'),
    path('holidays/<int:pk>/delete/',     views.holiday_delete,       name='holiday_delete'),

    path('security/',                     views.security_center,      name='security'),
    path('password-policy/',              views.password_policy,      name='password_policy'),
    path('login-history/',                views.login_history,        name='login_history'),
    path('audit-logs/',                   views.audit_logs,           name='audit_logs'),

    path('api/',                          views.api_settings,         name='api'),
    path('email/',                        views.email_settings,       name='email'),
    path('sms/',                          views.sms_settings,         name='sms'),
    path('payment-gateway/',              views.payment_gateway,      name='payment_gateway'),

    path('backup/',                       views.backup_center,        name='backup'),
    path('backup/new/',                   views.backup_new,           name='backup_new'),
    path('restore/',                      views.restore_center,       name='restore'),

    path('theme/',                        views.theme_settings,       name='theme'),
    path('language/',                     views.language_settings,    name='language'),
    path('currency/',                     views.currency_settings,    name='currency'),
]
