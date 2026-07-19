from django.urls import path
from . import views

app_name = 'portal'

urlpatterns = [
    path('',                              views.member_dashboard,     name='dashboard'),
    path('membership/',                   views.my_membership,        name='membership'),
    path('membership/renew/',             views.renew_membership,     name='renew'),
    path('membership/freeze/',            views.freeze_request,       name='freeze'),
    path('payments/',                     views.my_payments,          name='payments'),
    path('invoices/',                     views.my_invoices,          name='invoices'),
    path('attendance/',                   views.my_attendance,        name='attendance'),
    path('workout/',                      views.my_workout,           name='workout'),
    path('nutrition/',                    views.my_nutrition,         name='nutrition'),
    path('classes/',                      views.my_classes,           name='classes'),
    path('coach/',                        views.my_coach,             name='coach'),
    path('qr-code/',                      views.my_qr_code,           name='qr_code'),
    path('membership-card/',              views.membership_card,      name='card'),
    path('support/',                      views.support_tickets,      name='support'),
    path('support/new/',                  views.support_ticket_new,   name='support_new'),
    path('support/<int:pk>/',             views.support_ticket_detail,name='support_detail'),
    path('profile/',                      views.my_profile,           name='profile'),
]
