"""python manage.py seed_payments"""
import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.payments.models import Payment, Invoice, Receipt, CashRegister
from apps.members.models import Member
from apps.memberships.models import MemberSubscription
from apps.accounts.models import User


class Command(BaseCommand):
    help = 'Seed demo payments, invoices and cash registers'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\nSeeding payments...\n'))
        admin   = User.objects.filter(role='super_admin').first()
        members = list(Member.objects.filter(status='active'))
        today   = date.today()
        METHODS = ['cash','cash','cash','card','card','transfer']
        TYPES   = ['membership','membership','membership','registration','personal']
        created = 0

        for days_ago in range(30, 0, -1):
            day = today - timedelta(days=days_ago)
            daily_members = random.sample(members, min(random.randint(3,8), len(members)))
            reg, _ = CashRegister.objects.get_or_create(
                date=day,
                defaults={'opened_by': admin, 'status': 'closed' if days_ago > 0 else 'open',
                          'opening_balance': random.randint(500, 2000)}
            )
            for m in daily_members:
                if Payment.objects.filter(member=m, payment_date=day).exists(): continue
                method = random.choice(METHODS)
                amount = random.choice([250, 350, 450, 680, 800, 2400, 4500])
                pay = Payment.objects.create(
                    member=m, payment_type=random.choice(TYPES),
                    method=method, amount=amount, discount=0, tax=0,
                    payment_date=day, status='completed', received_by=admin,
                    reference=f'REF-{day.strftime("%Y%m%d")}-{m.pk:03d}',
                )
                Receipt.objects.create(payment=pay, issued_by=admin)
                created += 1

        # Seed pending/overdue invoices
        for m in random.sample(members, min(5, len(members))):
            sub = MemberSubscription.objects.filter(member=m, status='active').first()
            inv = Invoice(
                member=m, subscription=sub,
                due_date=today - timedelta(days=random.randint(1,15)),
                subtotal=sub.plan.price if sub else 500,
                discount_amount=0, tax_amount=0,
                status='overdue', created_by=admin,
            )
            inv.total = inv.subtotal
            inv.amount_paid = 0
            inv.save()

        self.stdout.write(self.style.SUCCESS(f'Done! {created} payments, {Invoice.objects.count()} invoices created.'))
