"""python manage.py seed_settings"""
import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.settings.models import SystemSettings, BusinessHours, Holiday, AuditLog, BackupRecord
from apps.accounts.models import User

class Command(BaseCommand):
    help = 'Seed settings & security demo data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\nSeeding settings...\n'))
        admin = User.objects.filter(role='super_admin').first()

        settings_obj = SystemSettings.load()
        settings_obj.gym_name = 'GymX Fitness Center'
        settings_obj.address = '123 El Gomhoria St, Mansoura, Egypt'
        settings_obj.phone = '01000000000'
        settings_obj.email = 'info@gymx.com'
        settings_obj.website = 'https://gymx.com'
        settings_obj.smtp_host = 'smtp.gmail.com'
        settings_obj.smtp_from_email = 'noreply@gymx.com'
        settings_obj.sms_provider = 'Twilio'
        settings_obj.payment_provider = 'Stripe'
        if not settings_obj.api_key:
            import secrets
            settings_obj.api_key = secrets.token_hex(24)
        settings_obj.save()

        for day_val, _ in BusinessHours.Day.choices:
            is_friday = (day_val == 4)
            BusinessHours.objects.get_or_create(day=day_val, defaults={
                'is_open': True,
                'open_time': '08:00' if is_friday else '06:00',
                'close_time': '22:00' if is_friday else '23:00',
            })

        Holiday.objects.get_or_create(name='New Year\'s Day', date=date(date.today().year,1,1), defaults={'is_recurring':True})
        Holiday.objects.get_or_create(name='Sham El-Nessim', date=date(date.today().year,4,21), defaults={'is_recurring':True})

        for i in range(5):
            AuditLog.objects.create(
                user=admin, action=random.choice(['create','update','login']),
                model_name=random.choice(['Member','Payment','Employee']),
                object_repr=f'Sample record #{i+1}', ip_address='127.0.0.1',
            )

        BackupRecord.objects.get_or_create(filename='gymx_backup_initial.sql', defaults={
            'size_mb':12.5, 'status':'completed', 'triggered_by':admin,
        })

        self.stdout.write(self.style.SUCCESS('Done! System settings, business hours, holidays, audit logs, and a backup seeded.'))
