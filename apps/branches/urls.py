from django.urls import path
from . import views

app_name = 'branches'

urlpatterns = [
    path('',                              views.branches_list,        name='list'),
    path('add/',                          views.branch_add,           name='add'),
    path('<int:pk>/',                     views.branch_detail,        name='detail'),
    path('<int:pk>/dashboard/',           views.branch_dashboard,      name='dashboard'),
    path('<int:pk>/employees/',           views.branch_employees,      name='employees'),
    path('<int:pk>/members/',             views.branch_members,        name='members'),
    path('<int:pk>/revenue/',             views.branch_revenue,        name='revenue'),
    path('<int:pk>/settings/',            views.branch_settings,       name='settings'),

    path('transfers/members/',            views.transfer_members,      name='transfer_members'),
    path('transfers/members/<int:pk>/action/', views.member_transfer_action, name='member_transfer_action'),
    path('transfers/employees/',          views.transfer_employees,    name='transfer_employees'),
    path('transfers/employees/<int:pk>/action/', views.employee_transfer_action, name='employee_transfer_action'),
]
