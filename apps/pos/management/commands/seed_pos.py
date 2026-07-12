"""python manage.py seed_pos"""
import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.pos.models import Sale, SaleItem, Discount, GiftCard
from apps.inventory.models import Product, Warehouse, Stock, StockMovement
from apps.members.models import Member
from apps.accounts.models import User

class Command(BaseCommand):
    help = 'Seed POS demo data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\nSeeding POS...\n'))
        admin   = User.objects.filter(role='super_admin').first()
        members = list(Member.objects.filter(status='active')[:15])
        products= list(Product.objects.filter(is_active=True, is_sellable=True))
        wh      = Warehouse.objects.first()
        today   = date.today()

        if not products:
            self.stdout.write(self.style.WARNING('No sellable products found — run seed_inventory first.'))
            return

        # Discount codes
        Discount.objects.get_or_create(code='WELCOME10', defaults={
            'description':'10% off for new members','discount_type':'percent',
            'value':10,'valid_until':today+timedelta(days=90),
        })
        Discount.objects.get_or_create(code='SAVE50', defaults={
            'description':'50 EGP off','discount_type':'fixed','value':50,
            'max_uses':100,
        })

        # Gift cards
        for i in range(3):
            GiftCard.objects.get_or_create(
                initial_amount=random.choice([200,500,1000]),
                purchased_by=random.choice(members) if members else None,
                defaults={'balance':random.choice([200,500,1000]), 'issued_to':f'Gift Recipient {i+1}', 'created_by':admin}
            )

        # Sales - last 20 days
        created = 0
        for days_ago in range(20, 0, -1):
            d = today - timedelta(days=days_ago)
            for _ in range(random.randint(2,6)):
                member = random.choice(members) if members and random.random() > 0.3 else None
                method = random.choice(['cash','cash','card','wallet'])
                sale = Sale.objects.create(
                    member=member, warehouse=wh, cashier=admin,
                    payment_method=method, status='completed',
                )
                sale.created_at = timezone.make_aware(timezone.datetime(d.year,d.month,d.day,random.randint(9,20),random.randint(0,59)))
                subtotal = 0
                for p in random.sample(products, min(random.randint(1,3), len(products))):
                    qty = random.randint(1,3)
                    SaleItem.objects.create(sale=sale, product=p, product_name=p.name, quantity=qty, unit_price=p.sale_price)
                    subtotal += qty * float(p.sale_price)
                sale.subtotal = subtotal
                sale.total = subtotal
                sale.amount_received = subtotal
                sale.save()
                created += 1

        self.stdout.write(self.style.SUCCESS(f'Done! {created} sales, 2 discount codes, 3 gift cards seeded.'))
