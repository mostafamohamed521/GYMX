"""python manage.py seed_aifeatures"""
from django.core.management.base import BaseCommand
from apps.aifeatures.models import ChatConversation, ChatMessage
from apps.accounts.models import User

class Command(BaseCommand):
    help = 'Seed AI features demo data (sample chat conversation)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\nSeeding AI features...\n'))
        admin = User.objects.filter(role='super_admin').first()
        if admin:
            conv, created = ChatConversation.objects.get_or_create(user=admin, defaults={'title':'Assistant Chat'})
            if created:
                ChatMessage.objects.create(conversation=conv, sender='user', message='Hi, how is revenue looking this month?')
                ChatMessage.objects.create(conversation=conv, sender='ai', message='You can find detailed revenue breakdowns under Reports → Revenue Reports, or check the Revenue Forecast page for projections.')
        self.stdout.write(self.style.SUCCESS('Done! Sample AI chat conversation seeded.'))
