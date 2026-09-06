from django.urls import path
from . import views

app_name = 'website'

urlpatterns = [
    path('',                              views.home,                 name='home'),
    path('about/',                        views.about_us,             name='about'),
    path('locations/',                    views.locations,            name='locations'),
    path('offers/',                       views.offers,               name='offers'),
    path('equipment/',                    views.equipment,            name='equipment'),
    path('gift-cards/',                   views.gift_cards,           name='gift_cards'),
    path('group-plans/',                  views.group_plans,          name='group_plans'),
    path('services/',                     views.services,             name='services'),
    path('membership-plans/',             views.membership_plans,     name='plans'),
    path('trainers/',                     views.trainers,             name='trainers'),
    path('trainers/<int:pk>/',            views.trainer_detail,       name='trainer_detail'),
    path('classes/',                      views.classes,              name='classes'),
    path('timetable/',                    views.timetable,            name='timetable'),
    path('gallery/',                      views.gallery,              name='gallery'),
    path('testimonials/',                 views.testimonials,         name='testimonials'),
    path('pricing/',                      views.pricing,              name='pricing'),
    path('blog/',                         views.blog,                 name='blog'),
    path('blog/<slug:slug>/',             views.blog_detail,          name='blog_detail'),
    path('events/',                       views.events,               name='events'),
    path('faq/',                          views.faq,                  name='faq'),
    path('contact/',                      views.contact_us,           name='contact'),
    path('careers/',                      views.careers,              name='careers'),
    path('careers/<int:pk>/apply/',       views.job_apply,            name='job_apply'),
    path('privacy-policy/',               views.privacy_policy,       name='privacy'),
    path('terms/',                        views.terms_conditions,     name='terms'),
]
