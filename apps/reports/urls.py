from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('',                              views.analytics_dashboard,   name='dashboard'),
    path('revenue/',                      views.revenue_reports,       name='revenue'),
    path('membership/',                   views.membership_reports,    name='membership'),
    path('attendance/',                   views.attendance_reports,    name='attendance'),
    path('payments/',                     views.payment_reports,       name='payments'),
    path('coaches/',                      views.coach_reports,         name='coaches'),
    path('employees/',                    views.employee_reports,      name='employees'),
    path('inventory/',                    views.inventory_reports,     name='inventory'),
    path('sales/',                        views.sales_reports,         name='sales'),
    path('profit-loss/',                  views.profit_loss,           name='profit_loss'),
    path('kpi/',                          views.kpi_dashboard,         name='kpi'),
    path('custom/',                       views.custom_reports,        name='custom'),
    path('custom/new/',                   views.custom_report_new,     name='custom_new'),
    path('export/',                       views.export_center,         name='export'),
    path('export/new/',                   views.export_new,            name='export_new'),
]
