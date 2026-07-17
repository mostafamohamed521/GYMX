"""python manage.py seed_notifications"""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.notifications.models import EmailTemplate, SMSTemplate, PushNotification, Announcement, ScheduledMessage
from apps.accounts.models import User, Notification
from apps.members.models import Member

class Command(BaseCommand):
    help = 'Seed notifications demo data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\nSeeding notifications...\n'))
        admin = User.objects.filter(role='super_admin').first()

        EmailTemplate.objects.get_or_create(name='Welcome Email', defaults={
            'purpose':'welcome','subject':'Welcome to GymX, {{member_name}}!',
            'body':'Hi {{member_name}}, welcome to GymX! We are excited to have you.',
        })
        EmailTemplate.objects.get_or_create(name='Membership Expiry Notice', defaults={
            'purpose':'expiry','subject':'Your membership expires on {{expiry_date}}',
            'body':'Hi {{member_name}}, your membership will expire on {{expiry_date}}. Renew now to keep your access!',
        })

        SMSTemplate.objects.get_or_create(name='Payment Reminder SMS', defaults={
            'purpose':'payment','body':'Hi {{member_name}}, your payment of {{amount}} EGP is due. Please visit the front desk.',
        })
        SMSTemplate.objects.get_or_create(name='Birthday SMS', defaults={
            'purpose':'birthday','body':'Happy Birthday {{member_name}}! 🎉 Enjoy a free smoothie on us today at GymX!',
        })

        PushNotification.objects.get_or_create(title='New Yoga Classes Added!', defaults={
            'message':'Check out our new morning yoga sessions starting this week.',
            'target_audience':'All members','status':'sent',
            'sent_at':timezone.now()-timedelta(days=2), 'recipients_count':Member.objects.count(),
            'created_by':admin,
        })

        Announcement.objects.get_or_create(title='Holiday Hours Update', defaults={
            'body':'GymX will operate on reduced hours (8AM-6PM) during the upcoming holiday.',
            'priority':'high','is_pinned':True,'created_by':admin,
        })

        ScheduledMessage.objects.get_or_create(name='Monthly Renewal Reminders', defaults={
            'channel':'email','target_audience':'Expiring memberships',
            'message':'Your membership renewal is due soon — renew today for 10% off!',
            'scheduled_for':timezone.now()+timedelta(days=3),'created_by':admin,
        })

        # A couple of sample in-app notifications for the admin
        if admin:
            Notification.objects.get_or_create(user=admin, title='Weekly Report Ready', defaults={
                'type':'info','message':'Your weekly business report is ready to view.',
            })

        self.stdout.write(self.style.SUCCESS('Done! Templates, push, announcements, and scheduled messages seeded.'))
