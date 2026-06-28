"""python manage.py seed_members — Seeds 20 demo members with full data."""
import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.members.models import (
    Member, EmergencyContact, MedicalInformation,
    BodyMeasurement, MemberNote, MemberGoal, MemberTimeline,
)
from apps.accounts.models import User

FIRST_NAMES = ['Ahmed','Sara','Mohamed','Nour','Omar','Layla','Karim','Hana','Youssef','Mona',
               'Ali','Rania','Hassan','Dina','Tarek','Aya','Mahmoud','Salma','Khaled','Mariam']
LAST_NAMES  = ['Hassan','Ibrahim','Mostafa','Khalil','Mahmoud','Ahmed','Ali','Saad','Farouk','Nasser']
BLOOD_TYPES = ['A+','A-','B+','B-','AB+','AB-','O+','O-']
STATUSES    = ['active','active','active','active','active','frozen','archived','blacklist']
LEVELS      = ['beginner','beginner','intermediate','intermediate','advanced','elite']
GENDERS     = ['male','male','female']
GOAL_TYPES  = ['weight_loss','muscle_gain','endurance','strength','flexibility','general']


class Command(BaseCommand):
    help = 'Seed 20 demo members with measurements, goals, notes, and timeline'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\nGymX — Seeding demo members...\n'))

        coach = User.objects.filter(role='coach').first()
        admin = User.objects.filter(role='super_admin').first()
        today = date.today()

        created = 0
        for i in range(20):
            fn   = FIRST_NAMES[i]
            ln   = random.choice(LAST_NAMES)
            gender = random.choice(GENDERS)
            status = random.choice(STATUSES) if i > 14 else 'active'
            level  = random.choice(LEVELS)

            member = Member.objects.create(
                first_name       = fn,
                last_name        = ln,
                email            = f'{fn.lower()}.{ln.lower()}{i}@gymx.demo',
                phone            = f'+20 10{random.randint(0,9)} {random.randint(100,999)} {random.randint(1000,9999)}',
                gender           = gender,
                birth_date       = today - timedelta(days=random.randint(365*18, 365*50)),
                nationality      = 'Egyptian',
                blood_type       = random.choice(BLOOD_TYPES),
                fitness_level    = level,
                status           = status,
                join_date        = today - timedelta(days=random.randint(30, 730)),
                assigned_coach   = coach,
                registered_by    = admin,
                occupation       = random.choice(['Engineer','Doctor','Teacher','Student','Business']),
                blacklist_reason = 'Repeated rule violations' if status == 'blacklist' else '',
                freeze_reason    = 'Medical leave' if status == 'frozen' else '',
                freeze_start     = today - timedelta(days=10) if status == 'frozen' else None,
                freeze_end       = today + timedelta(days=20) if status == 'frozen' else None,
            )

            # Generate QR
            try:
                member.generate_qr()
                member.save(update_fields=['qr_code'])
            except Exception:
                pass

            # Emergency contact
            EmergencyContact.objects.create(
                member=member,
                name=f'{random.choice(FIRST_NAMES)} {ln}',
                relationship=random.choice(['parent','spouse','sibling','friend']),
                phone=f'+20 11{random.randint(0,9)} {random.randint(100,999)} {random.randint(1000,9999)}',
                is_primary=True,
            )

            # Medical info
            h = random.randint(155, 195)
            w = random.randint(55, 110)
            MedicalInformation.objects.create(
                member=member,
                blood_type=member.blood_type,
                height_cm=h, weight_kg=w,
                chronic_conditions=random.choice(['None','Diabetes','Hypertension','']),
                allergies=random.choice(['None','Penicillin','']),
            )

            # 3 body measurements
            for j in range(3):
                d = today - timedelta(days=j*30)
                BodyMeasurement.objects.create(
                    member=member, date=d,
                    weight_kg=w - j*random.uniform(0,2),
                    height_cm=h,
                    chest_cm=random.uniform(85,110),
                    waist_cm=random.uniform(70,100),
                    hips_cm=random.uniform(85,110),
                    bicep_cm=random.uniform(28,42),
                    recorded_by=admin,
                )

            # Notes
            MemberNote.objects.create(
                member=member, title='Initial Assessment',
                body=f'{fn} joined at {level} level. Recommended starting program attached.',
                priority='normal', created_by=admin,
            )

            # Goal
            MemberGoal.objects.create(
                member=member,
                goal_type=random.choice(GOAL_TYPES),
                title=random.choice(['Lose 10kg','Gain muscle mass','Run 5K','Improve flexibility']),
                target_value=random.uniform(5,20),
                current_value=random.uniform(0,10),
                unit=random.choice(['kg','km','min']),
                target_date=today + timedelta(days=random.randint(60,180)),
                status='in_progress', created_by=admin,
            )

            # Timeline
            MemberTimeline.objects.create(
                member=member, event_type='joined',
                title='Member joined GymX',
                date=timezone.make_aware(timezone.datetime.combine(member.join_date, timezone.datetime.min.time())),
                created_by=admin,
            )
            MemberTimeline.objects.create(
                member=member, event_type='measurement',
                title='First measurements recorded',
                created_by=admin,
            )

            created += 1
            self.stdout.write(self.style.SUCCESS(f'  Created: {member.get_full_name()} [{member.member_id}] — {status}'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Done! {created} demo members created.'))
        self.stdout.write('')
