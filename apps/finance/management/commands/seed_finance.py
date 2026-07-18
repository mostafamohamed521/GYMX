"""python manage.py seed_finance"""
import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from apps.finance.models import Account, Income, Expense, Budget, TaxRecord, JournalEntry, JournalLine
from apps.accounts.models import User

ACCOUNTS = [
    ('1000','Cash on Hand','asset'),
    ('1010','Bank Account','asset'),
    ('2000','Accounts Payable','liability'),
    ('3000','Owner Equity','equity'),
    ('4000','Membership Revenue','income'),
    ('4010','POS Sales Revenue','income'),
    ('5000','Rent Expense','expense'),
    ('5010','Salaries Expense','expense'),
    ('5020','Utilities Expense','expense'),
]

class Command(BaseCommand):
    help = 'Seed finance demo data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\nSeeding finance...\n'))
        admin = User.objects.filter(role='super_admin').first()
        today = date.today()

        accounts = {}
        for code, name, atype in ACCOUNTS:
            a, _ = Account.objects.get_or_create(code=code, defaults={'name':name,'account_type':atype})
            accounts[code] = a

        # Income & Expense for last 60 days
        for days_ago in range(60, 0, -3):
            d = today - timedelta(days=days_ago)
            Income.objects.get_or_create(date=d, description=f'Membership payments — {d}', defaults={
                'category':'membership','amount':random.randint(3000,9000),
                'account':accounts['4000'],'recorded_by':admin,
            })
            Expense.objects.get_or_create(date=d, description=f'Utilities — {d}', defaults={
                'category':'utilities','amount':random.randint(200,900),'vendor':'Egypt Electricity Co.',
                'account':accounts['5020'],'recorded_by':admin,
            })

        Expense.objects.get_or_create(date=today.replace(day=1), description='Monthly Rent', defaults={
            'category':'rent','amount':15000,'vendor':'Property Management LLC',
            'account':accounts['5000'],'recorded_by':admin,
        })
        Expense.objects.get_or_create(date=today.replace(day=1), description='Staff Salaries', defaults={
            'category':'salaries','amount':45000,'account':accounts['5010'],'recorded_by':admin,
        })

        # Budgets
        Budget.objects.get_or_create(name='Monthly Utilities Budget', category='utilities', defaults={
            'period':'monthly','allocated_amount':3000,
            'start_date':today.replace(day=1), 'end_date':today.replace(day=28),
        })
        Budget.objects.get_or_create(name='Monthly Marketing Budget', category='marketing', defaults={
            'period':'monthly','allocated_amount':5000,
            'start_date':today.replace(day=1), 'end_date':today.replace(day=28),
        })

        # Tax record
        TaxRecord.objects.get_or_create(tax_type='vat', period_start=today.replace(day=1)-timedelta(days=30),
            period_end=today.replace(day=1)-timedelta(days=1), defaults={
            'taxable_amount':80000,'tax_rate':14,'tax_due':11200,'status':'pending',
        })

        # A sample journal entry
        entry, created = JournalEntry.objects.get_or_create(description='Opening balance', defaults={
            'date':today-timedelta(days=60), 'created_by':admin,
        })
        if created:
            JournalLine.objects.create(entry=entry, account=accounts['1000'], debit=50000, credit=0)
            JournalLine.objects.create(entry=entry, account=accounts['3000'], debit=0, credit=50000)

        self.stdout.write(self.style.SUCCESS('Done! Accounts, income, expenses, budgets, tax, and journal entries seeded.'))
