from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('',                              views.income_list,          name='income'),
    path('income/new/',                   views.income_new,           name='income_new'),
    path('expenses/',                     views.expenses_list,        name='expenses'),
    path('expenses/new/',                 views.expense_new,          name='expense_new'),
    path('transactions/',                 views.transactions,         name='transactions'),
    path('accounts/',                     views.accounts_list,        name='accounts'),
    path('accounts/new/',                 views.account_new,          name='account_new'),
    path('cash-flow/',                    views.cash_flow,            name='cash_flow'),
    path('budget/',                       views.budget_list,          name='budget'),
    path('budget/new/',                   views.budget_new,           name='budget_new'),
    path('taxes/',                        views.taxes_list,           name='taxes'),
    path('taxes/new/',                    views.tax_new,              name='tax_new'),
    path('statements/',                   views.financial_statements, name='statements'),
    path('journal/',                      views.journal_entries,      name='journal'),
    path('journal/new/',                  views.journal_new,          name='journal_new'),
    path('journal/<int:pk>/',             views.journal_detail,       name='journal_detail'),
    path('ledger/',                       views.general_ledger,       name='ledger'),
]
