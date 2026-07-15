"""
python manage.py link_demo_accounts

Links the demo `john@gymx.com` (member) and `ahmed.coach@gymx.com` (coach)
User accounts to real Member/Coach records, and seeds a bit of realistic
data for each so their role-based dashboards aren't empty.

Run this AFTER seed_demo, seed_members, seed_memberships, seed_attendance,
seed_payments, and seed_coaches. Safe to run multiple times.
"""
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from apps.accounts.models import User
from apps.members.models import Member
from apps.coaches.models import Coach
from apps.memberships.models import MembershipPlan, MemberSubscription
from apps.attendance.models import AttendanceRecord
from apps.payments.models import Payment
from apps.workouts.models import PTSession


class Command(BaseCommand):
    help = 'Link demo John/Ahmed accounts to Member/Coach records with sample data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\nLinking demo accounts...\n'))

        # ── Member demo account ──────────────────────────────
        john = User.objects.filter(email='john@gymx.com').first()
        if john:
            member, created = Member.objects.get_or_create(
                email='john@gymx.com',
                defaults={
                    'first_name': john.first_name or 'John', 'last_name': john.last_name or 'Smith',
                    'phone': '01000000001', 'status': 'active', 'user': john,
                }
            )
            if not member.user:
                member.user = john
                member.save(update_fields=['user'])

            plan = MembershipPlan.objects.first()
            if plan and not MemberSubscription.objects.filter(member=member, status='active').exists():
                MemberSubscription.objects.create(
                    member=member, plan=plan, status='active',
                    start_date=date.today() - timedelta(days=30), end_date=date.today() + timedelta(days=60),
                    original_price=plan.price, final_price=plan.price,
                )
            for days_ago in [1, 3, 5, 8, 12]:
                AttendanceRecord.objects.get_or_create(
                    member=member, date=date.today() - timedelta(days=days_ago),
                    defaults={'status': 'present'}
                )
            if plan:
                Payment.objects.get_or_create(
                    member=member, payment_date=date.today() - timedelta(days=25),
                    defaults={'payment_type': 'membership', 'method': 'cash', 'amount': plan.price,
                              'status': 'completed', 'received_by': john}
                )
            self.stdout.write(self.style.SUCCESS(f'  Member linked: {member} → {john.email}'))
        else:
            self.stdout.write(self.style.WARNING('  john@gymx.com not found — run seed_demo first.'))

        # ── Coach demo account ────────────────────────────────
        ahmed = User.objects.filter(email='ahmed.coach@gymx.com').first()
        if ahmed:
            coach, created = Coach.objects.get_or_create(
                email='ahmed.coach@gymx.com',
                defaults={
                    'first_name': ahmed.first_name or 'Ahmed', 'last_name': ahmed.last_name or 'Hassan',
                    'phone': '01000000002', 'status': 'active', 'user': ahmed,
                }
            )
            if not coach.user:
                coach.user = ahmed
                coach.save(update_fields=['user'])

            john_member = Member.objects.filter(user=john).first() if john else None
            others = Member.objects.exclude(pk=john_member.pk if john_member else None)[:4]
            for m in others:
                m.assigned_coach = ahmed
                m.save(update_fields=['assigned_coach'])

            if john_member:
                PTSession.objects.get_or_create(
                    member=john_member, coach=coach, date=date.today(),
                    defaults={'start_time': '10:00', 'end_time': '11:00', 'status': 'scheduled'}
                )
            self.stdout.write(self.style.SUCCESS(f'  Coach linked: {coach} → {ahmed.email} ({others.count()} members assigned)'))
        else:
            self.stdout.write(self.style.WARNING('  ahmed.coach@gymx.com not found — run seed_demo first.'))

        self.stdout.write(self.style.SUCCESS('\nDone!'))
