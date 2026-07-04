"""python manage.py seed_attendance"""
import random
from datetime import date, timedelta, datetime, time
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.attendance.models import AttendanceRecord, AttendanceSession, AttendanceSettings
from apps.members.models import Member
from apps.accounts.models import User

class Command(BaseCommand):
    help = 'Seed 30 days of demo attendance records'
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\nSeeding attendance...\n'))
        AttendanceSettings.get()
        admin   = User.objects.filter(role='super_admin').first()
        members = list(Member.objects.filter(status='active'))
        today   = date.today()
        created = 0
        METHODS = ['manual','manual','qr','qr','barcode']
        for days_ago in range(30,0,-1):
            day = today - timedelta(days=days_ago)
            count = random.randint(max(3,len(members)//3), min(len(members),len(members)))
            daily = random.sample(members, count)
            session, _ = AttendanceSession.objects.get_or_create(date=day, defaults={'is_open': day < today})
            for m in daily:
                if AttendanceRecord.objects.filter(member=m, date=day).exists(): continue
                h = random.randint(6,10); mi = random.randint(0,59)
                cin = timezone.make_aware(datetime.combine(day, time(h, mi)))
                cout = cin + timedelta(minutes=random.randint(30,180))
                AttendanceRecord.objects.create(
                    member=m, session=session, date=day,
                    check_in=cin, check_out=cout if random.random()>0.1 else None,
                    check_in_method=random.choice(METHODS),
                    status='late' if h >= 8 else 'present',
                    recorded_by=admin,
                )
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Done! {created} records created.'))
