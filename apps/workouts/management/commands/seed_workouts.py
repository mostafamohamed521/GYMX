"""python manage.py seed_workouts"""
import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from apps.workouts.models import Exercise, ExerciseCategory, WorkoutTemplate, WorkoutPlan, WorkoutSession, PTSession
from apps.members.models import Member
from apps.coaches.models import Coach
from apps.accounts.models import User

CATEGORIES = [
    ('Strength','fa-dumbbell','#3B82F6'),
    ('Cardio','fa-heart-pulse','#EF4444'),
    ('Flexibility','fa-person-praying','#8B5CF6'),
    ('Core','fa-circle','#F59E0B'),
    ('Functional','fa-arrows-rotate','#10B981'),
]

EXERCISES = [
    ('Barbell Bench Press','chest','barbell','intermediate',7),
    ('Pull-Up','back','bodyweight','intermediate',6),
    ('Squat','quads','barbell','intermediate',8),
    ('Deadlift','back','barbell','advanced',10),
    ('Overhead Press','shoulders','barbell','intermediate',6),
    ('Dumbbell Curl','biceps','dumbbell','beginner',4),
    ('Tricep Pushdown','triceps','cable','beginner',4),
    ('Plank','abs','bodyweight','beginner',3),
    ('Leg Press','quads','machine','beginner',7),
    ('Cable Row','back','cable','beginner',5),
    ('Lat Pulldown','back','machine','beginner',5),
    ('Incline Dumbbell Press','chest','dumbbell','intermediate',6),
    ('Hip Thrust','glutes','barbell','intermediate',6),
    ('Romanian Deadlift','hamstrings','barbell','intermediate',7),
    ('Treadmill Run','cardio','cardio_eq','beginner',10),
    ('Box Jump','quads','bodyweight','intermediate',9),
    ('Battle Ropes','full_body','none','intermediate',12),
    ('Mountain Climbers','abs','bodyweight','beginner',8),
    ('Dumbbell Row','back','dumbbell','beginner',5),
    ('Lateral Raise','shoulders','dumbbell','beginner',3),
]

TEMPLATES = [
    ('12-Week Muscle Gain','muscle_gain','intermediate',12,4,75),
    ('8-Week Fat Loss','weight_loss','beginner',8,3,45),
    ('Strength Foundation','strength','beginner',8,3,60),
    ('6-Week Endurance','endurance','intermediate',6,5,30),
    ('Full Body 3-Day','general','beginner',4,3,60),
]

class Command(BaseCommand):
    help = 'Seed workout demo data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\nSeeding workouts...\n'))
        admin   = User.objects.filter(role='super_admin').first()
        members = list(Member.objects.all()[:15])
        coaches = list(Coach.objects.all())
        today   = date.today()

        cats = {}
        for name, icon, color in CATEGORIES:
            c, _ = ExerciseCategory.objects.get_or_create(name=name, defaults={'icon':icon,'color':color})
            cats[name] = c

        cat_list = list(cats.values())
        exercises = []
        for name, muscle, equip, diff, cal in EXERCISES:
            ex, _ = Exercise.objects.get_or_create(name=name, defaults={
                'muscle_group':muscle,'equipment':equip,'difficulty':diff,
                'calories_per_min':cal,'category':random.choice(cat_list),
                'description':f'{name} is a great exercise for {muscle}.',
                'created_by':admin,
            })
            exercises.append(ex)

        for name, goal, diff, weeks, days, duration in TEMPLATES:
            WorkoutTemplate.objects.get_or_create(name=name, defaults={
                'goal':goal,'difficulty':diff,'duration_weeks':weeks,
                'days_per_week':days,'session_duration':duration,
                'is_public':True,'created_by':admin,
            })

        created_plans = 0
        for m in members:
            if WorkoutPlan.objects.filter(member=m).exists(): continue
            coach = random.choice(coaches) if coaches else None
            plan = WorkoutPlan.objects.create(
                member=m, coach=coach,
                name=random.choice(['Strength Program','Fat Loss Plan','Custom Training','General Fitness']),
                goal=random.choice(['muscle_gain','weight_loss','general','strength']),
                start_date=today - timedelta(days=random.randint(10,60)),
                status='active', created_by=admin,
            )
            for days_ago in range(20, 0, -5):
                d = today - timedelta(days=days_ago)
                status = 'completed' if days_ago > 2 else 'scheduled'
                WorkoutSession.objects.create(
                    plan=plan,
                    name=random.choice(['Upper Body','Lower Body','Full Body','Cardio Day']),
                    scheduled_date=d, status=status,
                    completed_date=d if status=='completed' else None,
                    duration_min=random.randint(45,75) if status=='completed' else None,
                    calories_burned=random.randint(200,500) if status=='completed' else None,
                )
            created_plans += 1

        # PT sessions
        for i in range(10):
            if members and coaches:
                PTSession.objects.get_or_create(
                    member=random.choice(members), coach=random.choice(coaches),
                    date=today + timedelta(days=random.randint(-5,14)),
                    defaults={
                        'start_time':f'{random.randint(7,17):02d}:00',
                        'end_time':f'{random.randint(8,18):02d}:00',
                        'status':random.choice(['scheduled','completed','scheduled']),
                    }
                )

        self.stdout.write(self.style.SUCCESS(f'Done! {created_plans} plans, {Exercise.objects.count()} exercises, {PTSession.objects.count()} PT sessions.'))
