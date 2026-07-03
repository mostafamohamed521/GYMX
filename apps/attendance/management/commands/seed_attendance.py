"""python manage.py seed_attendance — Seeds demo attendance records for the last 30 days."""
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
        self.stdout.write(self.style.MIGRATE_HEADING('\nGymX — Seeding attendance records...\n'))

        # Ensure settings exist
        AttendanceSettings.get()

        admin   = User.objects.filter(role='super_admin').first()
        members = list(Member.objects.filter(status='active'))
        today   = date.today()
        created = 0
        METHODS = ['manual', 'qr', 'qr', 'barcode', 'manual']

        for days_ago in range(30, 0, -1):
            day = today - timedelta(days=days_ago)

            # Skip some days (gym closed / low attendance)
            if day.weekday() == 4:  # Friday — reduced
                daily_members = random.sample(members, min(5, len(members)))
            else:
                count = random.randint(max(1, len(members)//3), min(len(members), len(members)))
                daily_members = random.sample(members, count)

            # Create session
            session, _ = AttendanceSession.objects.get_or_create(
                date=day,
                defaults={'is_open': day < today, 'opened_by': admin}
            )

            for member in daily_members:
                if AttendanceRecord.objects.filter(member=member, date=day).exists():
                    continue

                # Check-in between 06:30 and 11:00
                checkin_hour   = random.randint(6, 10)
                checkin_minute = random.randint(0, 59)
                checkin_dt     = timezone.make_aware(
                    datetime.combine(day, time(checkin_hour, checkin_minute))
                )

                # Duration 30min to 3 hours
                duration_min = random.randint(30, 180)
                checkout_dt  = checkin_dt + timedelta(minutes=duration_min)

                method = random.choice(METHODS)
                status = 'late' if checkin_hour >= 8 else 'present'

                AttendanceRecord.objects.create(
                    member          = member,
                    session         = session,
                    date            = day,
                    check_in        = checkin_dt,
                    check_out       = checkout_dt if random.random() > 0.1 else None,
                    check_in_method = method,
                    status          = status,
                    recorded_by     = admin,
                )
                created += 1

        self.stdout.write(self.style.SUCCESS(f'Done! {created} attendance records created.'))
        self.stdout.write(f'  Members: {Member.objects.filter(status="active").count()}')
        self.stdout.write(f'  Records: {AttendanceRecord.objects.count()}')
        self.stdout.write('')
