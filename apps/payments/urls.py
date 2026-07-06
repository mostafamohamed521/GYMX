from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Dashboard & Lists
    path('',                              views.revenue_dashboard,    name='dashboard'),
    path('list/',                         views.payment_list,         name='list'),
    path('pending/',                      views.pending_payments,     name='pending'),
    path('overdue/',                      views.overdue_payments,     name='overdue'),

    # Payment CRUD
    path('new/',                          views.payment_new,          name='new'),
    path('<int:pk>/',                     views.payment_detail,       name='detail'),

    # Invoices
    path('invoices/',                     views.invoice_list,         name='invoices'),
    path('invoices/new/',                 views.invoice_new,          name='invoice_new'),
    path('invoices/<int:pk>/',            views.invoice_detail,       name='invoice_detail'),

    # Receipts
    path('receipts/',                     views.receipt_list,         name='receipts'),
    path('receipts/<int:pk>/',            views.receipt_detail,       name='receipt_detail'),

    # Installments
    path('installments/',                 views.installment_list,     name='installments'),
    path('installments/new/',             views.installment_new,      name='installment_new'),
    path('installments/<int:pk>/',        views.installment_detail,   name='installment_detail'),
    path('installments/<int:pk>/pay/<int:inst_pk>/', views.installment_pay, name='installment_pay'),

    # Refunds
    path('refunds/',                      views.refund_list,          name='refunds'),
    path('refunds/new/<int:payment_pk>/', views.refund_new,           name='refund_new'),

    # Cash Register
    path('cash-register/',                views.daily_cash_register,  name='cash_register'),
    path('cash-register/close/',          views.daily_closing,        name='daily_closing'),

    # Reports
    path('reports/',                      views.payment_reports,      name='reports'),

    # AJAX
    path('ajax/member-info/<int:pk>/',    views.ajax_member_info,     name='ajax_member_info'),
]
