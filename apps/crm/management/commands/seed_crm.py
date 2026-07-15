"""python manage.py seed_crm"""
import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from apps.crm.models import (Lead, FollowUp, CallLog, Meeting, Feedback, Complaint,
                              Suggestion, LoyaltyTier, LoyaltyAccount, Referral, Campaign)
from apps.members.models import Member
from apps.accounts.models import User

LEADS = [
    ('Nourhan','Adel','01011112233','social','Weight loss'),
    ('Tarek','Younis','01022223344','walk_in','Muscle gain'),
    ('Salma','Kamal','01033334455','referral','General fitness'),
    ('Hossam','Zaki','01044445566','website','PT sessions'),
    ('Rania','Farid','01055556677','phone','Yoga classes'),
]

TIERS = [('Bronze',0,'#B45309'),('Silver',500,'#94A3B8'),('Gold',1500,'#F59E0B'),('Platinum',3000,'#8B5CF6')]

class Command(BaseCommand):
    help = 'Seed CRM demo data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\nSeeding CRM...\n'))
        admin   = User.objects.filter(role__in=['super_admin','receptionist']).first()
        members = list(Member.objects.filter(status='active')[:15])
        today   = date.today()

        tiers = []
        for name, min_pts, color in TIERS:
            t, _ = LoyaltyTier.objects.get_or_create(name=name, defaults={'min_points':min_pts,'color':color})
            tiers.append(t)

        leads = []
        for fn, ln, phone, source, interest in LEADS:
            l, created = Lead.objects.get_or_create(phone=phone, defaults={
                'first_name':fn,'last_name':ln,'source':source,'interest':interest,
                'status':random.choice(['new','contacted','qualified']),
                'assigned_to':admin,
            })
            leads.append(l)
            if created:
                FollowUp.objects.create(lead=l, scheduled_date=today+timedelta(days=random.randint(1,7)),
                                        notes='Initial follow-up call', assigned_to=admin)
                CallLog.objects.create(lead=l, direction='outbound', outcome='answered',
                                       duration_min=random.randint(2,10), called_by=admin)

        # Feedback
        for m in random.sample(members, min(6, len(members))):
            Feedback.objects.get_or_create(member=m, category=random.choice(['facility','staff','classes','general']), defaults={
                'rating':random.randint(3,5), 'comments':'Great experience overall!',
            })

        # Complaints
        for m in random.sample(members, min(3, len(members))):
            Complaint.objects.get_or_create(member=m, subject='Locker room cleanliness', defaults={
                'description':'The locker room needs more frequent cleaning.',
                'priority':random.choice(['low','medium','high']), 'assigned_to':admin,
            })

        # Suggestions
        Suggestion.objects.get_or_create(title='Add more yoga classes', defaults={
            'description':'Please add more morning yoga sessions.', 'votes':random.randint(5,20),
            'member': members[0] if members else None,
        })

        # Loyalty accounts
        for m in members:
            points = random.randint(0, 3500)
            tier = LoyaltyTier.objects.filter(min_points__lte=points).order_by('-min_points').first()
            LoyaltyAccount.objects.get_or_create(member=m, defaults={'points':points,'tier':tier})

        # Referrals
        for m in random.sample(members, min(4, len(members))):
            Referral.objects.get_or_create(referrer=m, referred_name=f'Friend of {m.first_name}', defaults={
                'referred_phone':'0100'+str(random.randint(1000000,9999999)),
                'status':random.choice(['pending','converted']),
                'reward_points':100,
            })

        # Campaigns
        Campaign.objects.get_or_create(name='Summer Membership Promo', defaults={
            'channel':'email','subject':'Get 20% off this summer!',
            'message':'Join now and save on annual memberships.',
            'target_audience':'All active members','status':'sent',
            'recipients_count':len(members), 'created_by':admin,
        })

        self.stdout.write(self.style.SUCCESS(f'Done! {len(leads)} leads, feedback, complaints, loyalty accounts seeded.'))
