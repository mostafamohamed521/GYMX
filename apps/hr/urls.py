from django.urls import path
from . import views

app_name = 'hr'

urlpatterns = [
    # Employees
    path('',                              views.employees_list,       name='list'),
    path('add/',                          views.employee_add,         name='add'),
    path('<int:pk>/',                     views.employee_detail,      name='detail'),

    # Departments / Positions / Roles / Permissions
    path('departments/',                  views.departments,          name='departments'),
    path('positions/',                    views.positions,            name='positions'),
    path('roles/',                        views.roles,                name='roles'),
    path('permissions/',                  views.permissions,          name='permissions'),
    path('permissions/<int:role_pk>/',    views.permissions_edit,     name='permissions_edit'),

    # Shifts
    path('shifts/',                       views.shift_management,     name='shifts'),

    # Attendance
    path('attendance/',                   views.employee_attendance,  name='attendance'),

    # Payroll
    path('payroll/',                      views.payroll,               name='payroll'),
    path('salaries/',                     views.salaries,              name='salaries'),
    path('bonuses/',                      views.bonuses,               name='bonuses'),
    path('deductions/',                   views.deductions,            name='deductions'),

    # Leave
    path('leave/',                        views.leave_requests,        name='leave'),
    path('leave/<int:pk>/action/',        views.leave_action,          name='leave_action'),

    # Performance
    path('performance/',                  views.performance_reviews,   name='performance'),
    path('performance/new/',              views.performance_new,       name='performance_new'),

    # Contracts
    path('contracts/',                    views.contracts,             name='contracts'),
    path('contracts/<int:pk>/download/',  views.contract_document_download, name='contract_download'),
    path('contracts/new/',                views.contract_new,          name='contract_new'),
]
