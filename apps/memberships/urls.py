from django.urls import path
from . import views

app_name = 'memberships'

urlpatterns = [
    # Plans
    path('',                          views.plan_list,           name='plans'),
    path('plans/add/',                views.plan_add,            name='plan_add'),
    path('plans/<int:pk>/',           views.plan_detail,         name='plan_detail'),
    path('plans/<int:pk>/edit/',      views.plan_edit,           name='plan_edit'),
    path('plans/<int:pk>/delete/',    views.plan_delete,         name='plan_delete'),

    # Categories
    path('categories/',               views.category_list,       name='categories'),
    path('categories/<int:pk>/edit/', views.category_edit,       name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete,   name='category_delete'),

    # Subscriptions by status
    path('active/',                   views.active_memberships,  name='active'),
    path('expired/',                  views.expired_memberships, name='expired'),
    path('frozen/',                   views.frozen_memberships,  name='frozen'),
    path('cancelled/',                views.cancelled_memberships,name='cancelled'),
    path('pending-renewals/',         views.pending_renewals,    name='pending_renewals'),

    # Subscription CRUD + actions
    path('subscriptions/add/',             views.subscription_add,    name='subscription_add'),
    path('subscriptions/<int:pk>/',        views.subscription_detail, name='subscription_detail'),
    path('subscriptions/<int:pk>/renew/',  views.renew_membership,    name='renew'),
    path('subscriptions/<int:pk>/upgrade/',views.upgrade_membership,  name='upgrade'),
    path('subscriptions/<int:pk>/transfer/',views.transfer_membership,name='transfer'),
    path('subscriptions/<int:pk>/freeze/', views.freeze_membership,   name='freeze'),
    path('subscriptions/<int:pk>/cancel/', views.cancel_membership,   name='cancel'),

    # Family
    path('family/',                   views.family_list,         name='family_list'),
    path('family/add/',               views.family_add,          name='family_add'),

    # Corporate
    path('corporate/',                views.corporate_list,      name='corporate_list'),
    path('corporate/add/',            views.corporate_add,       name='corporate_add'),

    # Discounts
    path('discounts/',                views.discount_list,       name='discounts'),
    path('discounts/<int:pk>/edit/',  views.discount_edit,       name='discount_edit'),
    path('discounts/<int:pk>/delete/',views.discount_delete,     name='discount_delete'),

    # Coupons
    path('coupons/',                  views.coupon_list,         name='coupons'),
    path('coupons/<int:pk>/delete/',  views.coupon_delete,       name='coupon_delete'),

    # Offers
    path('offers/',                   views.offer_list,          name='offers'),
    path('offers/<int:pk>/edit/',     views.offer_edit,          name='offer_edit'),
    path('offers/<int:pk>/delete/',   views.offer_delete,        name='offer_delete'),

    # Statistics
    path('statistics/',               views.statistics,          name='statistics'),
]
