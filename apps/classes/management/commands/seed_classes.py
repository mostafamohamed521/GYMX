"""python manage.py seed_classes"""
import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from apps.classes.models import ClassCategory, GymClass, ClassSchedule, ClassSession, ClassBooking
from apps.coaches.models import Coach
from apps.members.models import Member
from apps.accounts.models import User

CATEGORIES = [('Cardio','fa-heart-pulse','#EF4444'),('Strength','fa-dumbbell','#3B82F6'),('Mind & Body','fa-person-praying','#8B5CF6'),('Dance','fa-music','#EC4899')]

CLASSES = [
    ('Morning HIIT','Cardio','beginner',45,20,'#EF4444','Studio A',350),
    ('Power Yoga','Mind & Body','all',60,15,'#8B5CF6','Studio B',250),
    ('Spin Class','Cardio','intermediate',45,25,'#F59E0B','Cycle Room',400),
    ('CrossFit Bootcamp','Strength','advanced',60,15,'#3B82F6','Main Floor',500),
    ('Zumba Dance','Dance','all',50,30,'#EC4899','Studio A',300),
    ('Pilates Core','Mind & Body','beginner',45,18,'#10B981','Studio B',200),
]

class Command(BaseCommand):
    help = 'Seed classes demo data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\nSeeding classes...\n'))
        admin   = User.objects.filter(role='super_admin').first()
        coaches = list(Coach.objects.all())
        members = list(Member.objects.filter(status='active')[:20])
        today   = date.today()

        cats = {}
        for name, icon, color in CATEGORIES:
            c, _ = ClassCategory.objects.get_or_create(name=name, defaults={'icon':icon,'color':color})
            cats[name] = c

        classes = []
        for name, cat, diff, dur, cap, color, room, cal in CLASSES:
            cls, created = GymClass.objects.get_or_create(name=name, defaults={
                'category': cats.get(cat), 'coach': random.choice(coaches) if coaches else None,
                'difficulty': diff, 'duration_min': dur, 'max_capacity': cap,
                'color': color, 'room': room, 'calories_burn': cal,
                'description': f'{name} is a great {cat.lower()} class for all fitness levels.',
                'created_by': admin,
            })
            classes.append(cls)
            if created:
                for day in random.sample(range(7), 3):
                    hour = random.choice([7,9,17,18,19])
                    ClassSchedule.objects.get_or_create(gym_class=cls, day_of_week=day, defaults={
                        'start_time': f'{hour:02d}:00', 'end_time': f'{hour+1:02d}:00',
                    })

        created_sessions = 0
        for cls in classes:
            for days_ahead in range(-5, 15):
                d = today + timedelta(days=days_ahead)
                if random.random() > 0.6:
                    continue
                hour = random.choice([7,9,17,18,19])
                status = 'completed' if days_ahead < 0 else 'scheduled'
                session, created = ClassSession.objects.get_or_create(
                    gym_class=cls, date=d,
                    defaults={
                        'coach': cls.coach, 'start_time': f'{hour:02d}:00',
                        'end_time': f'{hour+1:02d}:00', 'status': status,
                    }
                )
                if created:
                    created_sessions += 1
                    n_bookings = random.randint(0, min(cls.max_capacity, len(members)))
                    for m in random.sample(members, n_bookings):
                        ClassBooking.objects.get_or_create(
                            session=session, member=m,
                            defaults={'status': 'attended' if status=='completed' else 'confirmed'}
                        )

        self.stdout.write(self.style.SUCCESS(f'Done! {len(classes)} classes, {created_sessions} sessions seeded.'))
