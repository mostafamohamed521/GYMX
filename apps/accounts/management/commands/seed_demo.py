"""python manage.py seed_demo — Creates demo users + sample notifications/activity."""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.accounts.models import User, Notification, ActivityLog

DEMO_USERS = [
    {'username':'superadmin','email':'superadmin@gymx.com','password':'GymX@2024','first_name':'Super','last_name':'Admin',
     'role':User.Role.SUPER_ADMIN,'is_staff':True,'is_superuser':True,'phone':'+20 100 000 0001','gender':User.Gender.MALE,
     'is_email_verified':True,'two_fa_enabled':True},
    {'username':'manager','email':'manager@gymx.com','password':'GymX@2024','first_name':'Khaled','last_name':'Hassan',
     'role':User.Role.GYM_MANAGER,'is_staff':True,'phone':'+20 100 000 0002','gender':User.Gender.MALE,'is_email_verified':True},
    {'username':'receptionist','email':'reception@gymx.com','password':'GymX@2024','first_name':'Sara','last_name':'Mostafa',
     'role':User.Role.RECEPTIONIST,'phone':'+20 100 000 0003','gender':User.Gender.FEMALE,'is_email_verified':True,'is_phone_verified':True},
    {'username':'coach_ahmed','email':'ahmed.coach@gymx.com','password':'GymX@2024','first_name':'Ahmed','last_name':'Ibrahim',
     'role':User.Role.COACH,'phone':'+20 100 000 0004','gender':User.Gender.MALE,'is_email_verified':True},
    {'username':'member_john','email':'john@gymx.com','password':'GymX@2024','first_name':'John','last_name':'Smith',
     'role':User.Role.MEMBER,'phone':'+20 100 000 0005','gender':User.Gender.MALE},
]


class Command(BaseCommand):
    help = 'Seed GymX demo users, notifications, and activity logs'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\nGymX — Seeding demo data...\n'))
        created = skipped = 0

        for data in DEMO_USERS:
            username = data['username']
            if User.objects.filter(username=username).exists():
                self.stdout.write(f'  Skipped (exists): {username}')
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

            # Seed notifications
            Notification.objects.create(user=user, type='success', title='Welcome to GymX!',
                message='Your account has been set up. Start by exploring the dashboard.')
            Notification.objects.create(user=user, type='info', title='Complete Your Profile',
                message='Add your profile photo and emergency contact information.')
            if user.role in [User.Role.GYM_MANAGER, User.Role.SUPER_ADMIN]:
                Notification.objects.create(user=user, type='warning', title='8 Memberships Expiring',
                    message='8 member memberships are expiring within the next 7 days.')
                Notification.objects.create(user=user, type='payment', title='Payment Received',
                    message='Payment of $120 received from member John Smith.')

            # Seed activity logs
            ActivityLog.objects.create(user=user, action='register', description='Account created via seeder',
                ip_address='127.0.0.1')
            ActivityLog.objects.create(user=user, action='login', description='First login',
                ip_address='127.0.0.1')

            created += 1
            self.stdout.write(self.style.SUCCESS(f'  Created: {user.get_full_name()} ({user.get_role_display()})'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Done! Created: {created} | Skipped: {skipped}'))
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('Demo credentials (all use password: GymX@2024):'))
        self.stdout.write('  superadmin   → Super Admin')
        self.stdout.write('  manager      → Gym Manager')
        self.stdout.write('  receptionist → Receptionist')
        self.stdout.write('  coach_ahmed  → Coach')
        self.stdout.write('  member_john  → Member')
        self.stdout.write('')
