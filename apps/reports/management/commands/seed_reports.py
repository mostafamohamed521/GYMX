"""python manage.py seed_reports"""
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from apps.reports.models import SavedReport, ExportLog
from apps.accounts.models import User

class Command(BaseCommand):
    help = 'Seed reports demo data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\nSeeding reports...\n'))
        admin = User.objects.filter(role='super_admin').first()
        today = date.today()

        SavedReport.objects.get_or_create(name='Q2 Revenue Summary', defaults={
            'report_type':'revenue', 'date_from':today-timedelta(days=90), 'date_to':today,
            'created_by':admin,
        })
        SavedReport.objects.get_or_create(name='Monthly Attendance Overview', defaults={
            'report_type':'attendance', 'date_from':today-timedelta(days=30), 'date_to':today,
            'created_by':admin,
        })
        ExportLog.objects.get_or_create(report_name='Revenue Report — June', defaults={
            'format':'pdf', 'status':'completed', 'requested_by':admin,
        })
        ExportLog.objects.get_or_create(report_name='Member List Export', defaults={
            'format':'xlsx', 'status':'completed', 'requested_by':admin,
        })

        self.stdout.write(self.style.SUCCESS('Done! 2 saved reports, 2 export logs seeded.'))
