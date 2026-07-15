from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    path('',                              views.leads_list,           name='leads'),
    path('leads/new/',                    views.lead_new,             name='lead_new'),
    path('leads/<int:pk>/',               views.lead_detail,          name='lead_detail'),
    path('leads/<int:pk>/convert/',       views.lead_convert,         name='lead_convert'),
    path('prospects/',                    views.prospects,            name='prospects'),

    path('follow-ups/',                   views.follow_ups,           name='follow_ups'),
    path('follow-ups/<int:pk>/complete/', views.follow_up_complete,   name='follow_up_complete'),

    path('calls/',                        views.call_logs,            name='calls'),
    path('meetings/',                     views.meetings,             name='meetings'),

    path('feedback/',                     views.feedback_list,        name='feedback'),
    path('complaints/',                   views.complaints,           name='complaints'),
    path('complaints/<int:pk>/',          views.complaint_detail,     name='complaint_detail'),
    path('suggestions/',                  views.suggestions,          name='suggestions'),
    path('suggestions/<int:pk>/vote/',    views.suggestion_vote,      name='suggestion_vote'),

    path('loyalty/',                      views.loyalty_program,      name='loyalty'),
    path('loyalty/<int:pk>/add-points/',  views.loyalty_add_points,   name='loyalty_add_points'),
    path('referrals/',                    views.referral_program,     name='referrals'),
    path('campaigns/',                    views.campaigns,            name='campaigns'),
    path('campaigns/new/',                views.campaign_new,         name='campaign_new'),
]
