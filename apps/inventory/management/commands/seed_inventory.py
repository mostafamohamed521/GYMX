"""python manage.py seed_inventory"""
import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from apps.inventory.models import (ProductCategory, Brand, Supplier, Warehouse,
                                    Product, Stock, StockMovement, PurchaseOrder,
                                    PurchaseOrderItem, Equipment, EquipmentMaintenance)
from apps.accounts.models import User

CATEGORIES = [('Supplements','fa-pills','#8B5CF6'),('Apparel','fa-shirt','#EC4899'),
              ('Accessories','fa-dumbbell','#3B82F6'),('Beverages','fa-bottle-water','#10B981'),
              ('Cardio Equipment','fa-heart-pulse','#EF4444'),('Strength Equipment','fa-weight-hanging','#F59E0B')]

BRANDS = ['Optimum Nutrition','Under Armour','Technogym','Life Fitness','MuscleTech','Nike']

PRODUCTS = [
    ('Whey Protein 2kg','Supplements','Optimum Nutrition',850,1200),
    ('Gym T-Shirt','Apparel','Under Armour',120,250),
    ('Shaker Bottle','Accessories','Nike',35,80),
    ('Energy Drink','Beverages','MuscleTech',15,35),
    ('Resistance Bands Set','Accessories','Nike',80,180),
    ('Creatine Monohydrate','Supplements','MuscleTech',280,450),
    ('Gym Gloves','Apparel','Under Armour',60,120),
    ('Protein Bar','Supplements','Optimum Nutrition',20,45),
]

EQUIPMENT = [
    ('Treadmill Pro X','Cardio Equipment','Technogym',85000),
    ('Elliptical Machine','Cardio Equipment','Life Fitness',65000),
    ('Cable Crossover Station','Strength Equipment','Technogym',95000),
    ('Olympic Barbell Set','Strength Equipment','Life Fitness',12000),
    ('Rowing Machine','Cardio Equipment','Technogym',45000),
]

class Command(BaseCommand):
    help = 'Seed inventory demo data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\nSeeding inventory...\n'))
        admin = User.objects.filter(role='super_admin').first()
        today = date.today()

        cats = {}
        for name, icon, color in CATEGORIES:
            c, _ = ProductCategory.objects.get_or_create(name=name, defaults={'icon':icon,'color':color})
            cats[name] = c

        brands = {}
        for name in BRANDS:
            b, _ = Brand.objects.get_or_create(name=name)
            brands[name] = b

        wh, _ = Warehouse.objects.get_or_create(name='Main Warehouse', defaults={'location':'Ground Floor'})
        wh2, _ = Warehouse.objects.get_or_create(name='Storage Room', defaults={'location':'Basement'})

        supplier, _ = Supplier.objects.get_or_create(name='FitSupply Egypt', defaults={
            'contact_person':'Ahmed Sayed','phone':'01099998888','email':'sales@fitsupply.eg',
        })

        products = []
        for name, cat, brand, cost, sale in PRODUCTS:
            p, created = Product.objects.get_or_create(name=name, defaults={
                'category':cats[cat],'brand':brands[brand],
                'cost_price':cost,'sale_price':sale,'reorder_level':10,
                'created_by':admin,
            })
            products.append(p)
            if created:
                qty = random.randint(5, 60)
                Stock.objects.create(product=p, warehouse=wh, quantity=qty)
                StockMovement.objects.create(product=p, warehouse=wh, move_type='in', quantity=qty, reference='Initial stock', performed_by=admin)

        equipment_list = []
        for name, cat, brand, price in EQUIPMENT:
            eq, created = Equipment.objects.get_or_create(name=name, defaults={
                'category':cats[cat],'brand':brands[brand],
                'purchase_date':today - timedelta(days=random.randint(100,700)),
                'purchase_price':price,
                'warranty_until':today + timedelta(days=random.randint(-30,400)),
                'location':random.choice(['Main Floor','Cardio Zone','Weight Room']),
                'status':'operational',
            })
            equipment_list.append(eq)
            if created:
                EquipmentMaintenance.objects.create(
                    equipment=eq, maintenance_type='routine',
                    status='completed', scheduled_date=today-timedelta(days=30),
                    completed_date=today-timedelta(days=28), cost=random.randint(200,800),
                    technician='Mahmoud Ali',
                )

        # Purchase order
        po, created = PurchaseOrder.objects.get_or_create(supplier=supplier, defaults={
            'warehouse':wh,'status':'received','order_date':today-timedelta(days=15),
            'expected_date':today-timedelta(days=5),'created_by':admin,
        })
        if created:
            total = 0
            for p in products[:3]:
                qty = random.randint(10,30)
                PurchaseOrderItem.objects.create(po=po, product=p, quantity=qty, unit_price=p.cost_price)
                total += qty * float(p.cost_price)
            po.total_amount = total
            po.save()

        self.stdout.write(self.style.SUCCESS(f'Done! {len(products)} products, {len(equipment_list)} equipment items seeded.'))
