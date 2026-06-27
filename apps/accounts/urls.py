from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Landing
    path('',          views.splash_view,  name='splash'),
    path('welcome/',   views.welcome_view, name='welcome'),

    # Public
    path('login/',          views.login_view,           name='login'),
    path('logout/',         views.logout_view,          name='logout'),
    path('forgot-password/',views.forgot_password_view, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password_view, name='reset_password'),

    # Registration
    path('register/member/',   views.register_member_view,   name='register_member'),
    path('register/staff/',    views.register_staff_view,    name='register_staff'),
    path('register/complete/', views.complete_registration_view, name='complete_registration'),

    # Verification
    path('verify/email/',      views.email_verification_view, name='email_verification'),
    path('verify/email/resend/', views.resend_otp_view,       name='resend_otp'),
    path('verify/phone/',      views.phone_otp_view,          name='phone_otp'),

    # Auth features
    path('change-password/',   views.change_password_view,   name='change_password'),
    path('two-factor-auth/',   views.two_fa_view,             name='two_fa'),

    # Profile
    path('profile/',           views.profile_view,            name='profile'),
    path('profile/edit/',      views.profile_edit_view,       name='profile_edit'),
    path('preferences/',       views.preferences_view,        name='preferences'),

    # Sessions
    path('sessions/',          views.session_management_view, name='session_management'),
    path('sessions/<int:session_id>/revoke/', views.revoke_session_view, name='revoke_session'),
    path('sessions/revoke-all/',              views.revoke_all_sessions_view, name='revoke_all_sessions'),

    # History & Logs
    path('login-history/',     views.login_history_view,      name='login_history'),
    path('activity/',          views.activity_log_view,        name='activity_log'),

    # Notifications
    path('notifications/',     views.notifications_view,                      name='notifications'),
    path('notifications/<int:pk>/read/', views.mark_notification_read_view,   name='mark_notification_read'),
    path('notifications/clear/',         views.clear_all_notifications_view,  name='clear_notifications'),
]
