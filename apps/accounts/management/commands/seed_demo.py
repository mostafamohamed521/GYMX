"""
python manage.py seed_demo
Creates demo users for all roles.
"""
from django.core.management.base import BaseCommand
from apps.accounts.models import User


DEMO_USERS = [
    {
        'username': 'superadmin',
        'email': 'superadmin@gymx.com',
        'password': 'GymX@2024',
        'first_name': 'Super',
        'last_name': 'Admin',
        'role': User.Role.SUPER_ADMIN,
        'is_staff': True,
        'is_superuser': True,
        'phone': '+20 100 000 0001',
        'gender': User.Gender.MALE,
    },
    {
        'username': 'manager',
        'email': 'manager@gymx.com',
        'password': 'GymX@2024',
        'first_name': 'Khaled',
        'last_name': 'Hassan',
        'role': User.Role.GYM_MANAGER,
        'is_staff': True,
        'phone': '+20 100 000 0002',
        'gender': User.Gender.MALE,
    },
    {
        'username': 'receptionist',
        'email': 'reception@gymx.com',
        'password': 'GymX@2024',
        'first_name': 'Sara',
        'last_name': 'Mostafa',
        'role': User.Role.RECEPTIONIST,
        'phone': '+20 100 000 0003',
        'gender': User.Gender.FEMALE,
    },
    {
        'username': 'coach_ahmed',
        'email': 'ahmed.coach@gymx.com',
        'password': 'GymX@2024',
        'first_name': 'Ahmed',
        'last_name': 'Ibrahim',
        'role': User.Role.COACH,
        'phone': '+20 100 000 0004',
        'gender': User.Gender.MALE,
    },
    {
        'username': 'member_john',
        'email': 'john@gymx.com',
        'password': 'GymX@2024',
        'first_name': 'John',
        'last_name': 'Smith',
        'role': User.Role.MEMBER,
        'phone': '+20 100 000 0005',
        'gender': User.Gender.MALE,
    },
]


class Command(BaseCommand):
    help = 'Seed GymX with demo users for all roles'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\n🏋️  GymX — Seeding demo users...\n'))

        created = 0
        skipped = 0

        for data in DEMO_USERS:
            username = data['username']
            if User.objects.filter(username=username).exists():
                self.stdout.write(f'  ⚠️  Skipped (exists): {username}')
                skipped += 1
                continue

            is_super = data.pop('is_superuser', False)
            is_staff = data.pop('is_staff', False)
            password = data.pop('password')

            user = User(**data)
            user.set_password(password)
            user.is_staff = is_staff
            user.is_superuser = is_super
            user.save()

            created += 1
            self.stdout.write(
                self.style.SUCCESS(f'  ✅ Created: {user.get_full_name()} ({user.get_role_display()})')
            )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Done! Created: {created} | Skipped: {skipped}'))
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('Demo credentials:'))
        self.stdout.write('  Username: superadmin   Password: GymX@2024  (Super Admin)')
        self.stdout.write('  Username: manager      Password: GymX@2024  (Gym Manager)')
        self.stdout.write('  Username: receptionist Password: GymX@2024  (Receptionist)')
        self.stdout.write('  Username: coach_ahmed  Password: GymX@2024  (Coach)')
        self.stdout.write('  Username: member_john  Password: GymX@2024  (Member)')
        self.stdout.write('')
