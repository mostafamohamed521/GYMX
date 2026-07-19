"""python manage.py seed_portal"""
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from apps.portal.models import SupportTicket, TicketReply, FreezeRequest, RenewalRequest
from apps.members.models import Member
from apps.accounts.models import User

class Command(BaseCommand):
    help = 'Seed member portal demo data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\nSeeding member portal...\n'))
        john = User.objects.filter(email='john@gymx.com').first()
        member = Member.objects.filter(user=john).first() if john else Member.objects.first()
        admin  = User.objects.filter(role='super_admin').first()

        if not member:
            self.stdout.write(self.style.WARNING('No member found — run link_demo_accounts first.'))
            return

        ticket, created = SupportTicket.objects.get_or_create(member=member, subject='Locker key replacement', defaults={
            'description':'I lost my locker key and need a replacement.',
            'category':'facility','status':'in_progress','assigned_to':admin,
        })
        if created:
            TicketReply.objects.create(ticket=ticket, author=admin, message='We will issue a new key at the front desk. Please bring your ID.', is_staff_reply=True)

        FreezeRequest.objects.get_or_create(member=member, start_date=date.today()+timedelta(days=10), end_date=date.today()+timedelta(days=20), defaults={
            'reason':'Traveling abroad for work.', 'status':'pending',
        })

        RenewalRequest.objects.get_or_create(member=member, defaults={'status':'pending','notes':'Please renew for another 3 months.'})

        self.stdout.write(self.style.SUCCESS('Done! Sample support ticket, freeze request, and renewal request seeded.'))
