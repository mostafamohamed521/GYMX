"""python manage.py seed_memberships — Seeds plans, categories, discounts, and demo subscriptions."""
import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.memberships.models import (
    MembershipCategory, MembershipPlan, MemberSubscription,
    Discount, Coupon, Offer,
)
from apps.members.models import Member
from apps.accounts.models import User


CATEGORIES = [
    {'name': 'Basic',     'color': '#3B82F6', 'icon': 'fa-id-card',     'sort_order': 1},
    {'name': 'Premium',   'color': '#8B5CF6', 'icon': 'fa-star',         'sort_order': 2},
    {'name': 'VIP',       'color': '#F59E0B', 'icon': 'fa-crown',        'sort_order': 3},
    {'name': 'Special',   'color': '#10B981', 'icon': 'fa-bolt',         'sort_order': 4},
]

PLANS = [
    # Basic
    {'name': 'Basic Monthly',   'plan_type': 'standard', 'billing_cycle': 'monthly',   'duration_days': 30,  'price': 250,  'cat': 'Basic',   'features': ['Full gym access','Locker room','Basic equipment'], 'is_featured': False},
    {'name': 'Basic Quarterly', 'plan_type': 'standard', 'billing_cycle': 'quarterly', 'duration_days': 90,  'price': 680,  'cat': 'Basic',   'features': ['Full gym access','Locker room','Basic equipment','10% savings'], 'is_featured': False},
    {'name': 'Basic Annual',    'plan_type': 'standard', 'billing_cycle': 'annual',    'duration_days': 365, 'price': 2400, 'cat': 'Basic',   'features': ['Full gym access','Locker room','Basic equipment','20% savings','1 guest pass/month'], 'is_featured': False},
    # Premium
    {'name': 'Premium Monthly',  'plan_type': 'premium', 'billing_cycle': 'monthly',  'duration_days': 30,  'price': 450,  'cat': 'Premium', 'features': ['Everything in Basic','Personal trainer session','Nutrition consultation','Sauna & steam room','Group classes'], 'is_featured': True},
    {'name': 'Premium Annual',   'plan_type': 'premium', 'billing_cycle': 'annual',   'duration_days': 365, 'price': 4500, 'cat': 'Premium', 'features': ['Everything in Basic','12 PT sessions/year','Unlimited group classes','Sauna & steam room','2 guest passes/month'], 'is_featured': True},
    # VIP
    {'name': 'VIP Monthly',      'plan_type': 'vip',     'billing_cycle': 'monthly',  'duration_days': 30,  'price': 800,  'cat': 'VIP',     'features': ['All Premium features','Dedicated coach','Meal plan','Priority booking','Towel service','Parking'], 'is_featured': True},
    # Special
    {'name': 'Student Plan',     'plan_type': 'student', 'billing_cycle': 'monthly',  'duration_days': 30,  'price': 150,  'cat': 'Special', 'features': ['Full gym access','Student ID required','Valid equipment access'], 'is_featured': False},
    {'name': 'Senior Plan',      'plan_type': 'senior',  'billing_cycle': 'monthly',  'duration_days': 30,  'price': 180,  'cat': 'Special', 'features': ['Full gym access','Age 55+','Specialised equipment'], 'is_featured': False},
    {'name': 'Family Plan',      'plan_type': 'family',  'billing_cycle': 'monthly',  'duration_days': 30,  'price': 900,  'cat': 'Special', 'features': ['Up to 4 members','Full gym access','10% per extra member'], 'max_members': 4, 'is_featured': False},
    {'name': '3-Day Trial',      'plan_type': 'trial',   'billing_cycle': 'daily',    'duration_days': 3,   'price': 50,   'cat': 'Special', 'features': ['3-day access','Full gym access','No commitment'], 'is_featured': False},
]


class Command(BaseCommand):
    help = 'Seed membership categories, plans, discounts, and demo subscriptions'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\nGymX — Seeding memberships...\n'))

        admin = User.objects.filter(role='super_admin').first()
        today = date.today()

        # ── Categories ─────────────────────────────────────
        cats = {}
        for data in CATEGORIES:
            cat, created = MembershipCategory.objects.get_or_create(
                name=data['name'],
                defaults={k: v for k, v in data.items() if k != 'name'}
            )
            cats[cat.name] = cat
            status = 'Created' if created else 'Exists '
            self.stdout.write(f'  {status}: Category — {cat.name}')

        # ── Plans ───────────────────────────────────────────
        plans = {}
        for data in PLANS:
            cat_name = data.pop('cat')
            feat     = data.pop('features', [])
            existing = MembershipPlan.objects.filter(name=data['name']).first()
            if existing:
                self.stdout.write(f'  Exists : Plan — {data["name"]}')
                plans[data['name']] = existing
                continue
            plan = MembershipPlan.objects.create(
                category=cats.get(cat_name),
                features=feat,
                created_by=admin,
                is_active=True,
                is_public=True,
                max_freeze_days=30,
                setup_fee=0,
                sort_order=list(plans.keys().__len__().__class__().__class__.mro()).index(type(0)),
                **data
            )
            plans[plan.name] = plan
            self.stdout.write(self.style.SUCCESS(f'  Created: Plan — {plan.name} ({plan.price} EGP)'))

        # ── Discounts ───────────────────────────────────────
        disc_data = [
            {'name': 'Summer20', 'discount_type': 'percentage', 'value': 20,
             'valid_from': today, 'valid_until': today + timedelta(days=90),
             'usage_limit': 50, 'is_active': True, 'description': 'Summer promotional discount'},
            {'name': '100 EGP Off', 'discount_type': 'fixed', 'value': 100,
             'valid_from': today, 'valid_until': today + timedelta(days=30),
             'usage_limit': 20, 'is_active': True, 'description': 'Fixed amount off any plan'},
            {'name': 'Referral15', 'discount_type': 'percentage', 'value': 15,
             'is_active': True, 'description': 'Referral program discount'},
        ]
        for dd in disc_data:
            d, c = Discount.objects.get_or_create(name=dd['name'], defaults={**dd, 'created_by': admin})
            self.stdout.write(('  Created' if c else '  Exists ') + f': Discount — {d.name}')

        # ── Coupons ─────────────────────────────────────────
        disc = Discount.objects.first()
        if disc:
            for code in ['SUMMER25', 'GYM10OFF', 'WELCOME50']:
                c, cr = Coupon.objects.get_or_create(
                    code=code,
                    defaults={'discount': disc, 'is_active': True,
                              'valid_until': today + timedelta(days=60), 'created_by': admin}
                )
                self.stdout.write(('  Created' if cr else '  Exists ') + f': Coupon — {c.code}')

        # ── Offers ──────────────────────────────────────────
        if not Offer.objects.exists():
            Offer.objects.create(
                name='Summer Special',
                offer_type='seasonal',
                description='Get 20% off all premium plans this summer!',
                valid_from=today,
                valid_until=today + timedelta(days=60),
                is_active=True,
                is_featured=True,
                created_by=admin,
            )
            self.stdout.write(self.style.SUCCESS('  Created: Offer — Summer Special'))

        # ── Demo Subscriptions ──────────────────────────────
        members = list(Member.objects.filter(status='active')[:15])
        plan_list = list(MembershipPlan.objects.filter(is_active=True))
        if members and plan_list:
            sub_count = 0
            for member in members:
                if MemberSubscription.objects.filter(member=member, status='active').exists():
                    continue
                plan = random.choice(plan_list)
                start = today - timedelta(days=random.randint(5, 60))
                end   = start + timedelta(days=plan.duration_days)
                payment_status = random.choice(['paid', 'paid', 'paid', 'unpaid', 'partial'])
                amount_paid = float(plan.price) if payment_status == 'paid' else (
                    float(plan.price) * 0.5 if payment_status == 'partial' else 0
                )
                sub = MemberSubscription.objects.create(
                    member=member, plan=plan,
                    status='active' if end >= today else 'expired',
                    payment_status=payment_status,
                    start_date=start, end_date=end,
                    original_price=plan.price,
                    discount_amount=0,
                    final_price=plan.price,
                    amount_paid=amount_paid,
                    created_by=admin,
                )
                sub_count += 1

            self.stdout.write(self.style.SUCCESS(f'\n  Created {sub_count} demo subscriptions'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Memberships seeding complete!'))
        self.stdout.write(f'  Categories: {MembershipCategory.objects.count()}')
        self.stdout.write(f'  Plans:      {MembershipPlan.objects.count()}')
        self.stdout.write(f'  Discounts:  {Discount.objects.count()}')
        self.stdout.write(f'  Coupons:    {Coupon.objects.count()}')
        self.stdout.write(f'  Subs:       {MemberSubscription.objects.count()}')
        self.stdout.write('')
