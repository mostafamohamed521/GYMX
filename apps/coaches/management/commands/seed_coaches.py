"""python manage.py seed_coaches"""
import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.coaches.models import Coach, CoachSpecialization, CoachCertificate, CoachNote, CoachAvailability, CoachSchedule, CoachAttendance, CoachSalary
from apps.members.models import Member
from apps.accounts.models import User


SPECS = [
    ('Strength Training','fa-dumbbell','#3B82F6'),
    ('Cardio','fa-heart-pulse','#EF4444'),
    ('Yoga','fa-person-praying','#8B5CF6'),
    ('HIIT','fa-fire','#F59E0B'),
    ('Nutrition','fa-apple-whole','#10B981'),
    ('Boxing','fa-hand-fist','#EC4899'),
    ('CrossFit','fa-medal','#06B6D4'),
    ('Swimming','fa-person-swimming','#0EA5E9'),
]

COACHES_DATA = [
    ('Ahmed','Hassan','ahmed.hassan@gymx.com','01001234567','male','1990-03-15','Egyptian',5800,8,4.8),
    ('Sara','Khalil','sara.khalil@gymx.com','01112345678','female','1993-07-22','Egyptian',5200,6,4.9),
    ('Mohamed','Fathy','m.fathy@gymx.com','01223456789','male','1988-11-05','Egyptian',6500,10,4.7),
    ('Nour','Samir','nour.samir@gymx.com','01334567890','female','1995-02-18','Egyptian',4800,4,4.6),
    ('Karim','Mansour','k.mansour@gymx.com','01045678901','male','1987-09-30','Egyptian',7200,12,4.9),
]

class Command(BaseCommand):
    help = 'Seed demo coaches data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\nSeeding coaches...\n'))
        admin   = User.objects.filter(role='super_admin').first()
        members = list(Member.objects.all()[:20])
        today   = date.today()

        # Specializations
        specs = []
        for name, icon, color in SPECS:
            s, _ = CoachSpecialization.objects.get_or_create(name=name, defaults={'icon':icon,'color':color})
            specs.append(s)

        coaches = []
        for fn, ln, email, phone, gender, bdate, nat, salary, exp, rating in COACHES_DATA:
            if Coach.objects.filter(email=email).exists():
                coaches.append(Coach.objects.get(email=email))
                continue
            c = Coach.objects.create(
                first_name=fn, last_name=ln, email=email, phone=phone,
                gender=gender, birth_date=bdate, nationality=nat,
                status='active', employment_type=random.choice(['full_time','part_time']),
                hire_date=today - timedelta(days=random.randint(180,1000)),
                experience_years=exp, base_salary=salary,
                commission_rate=random.choice([5,8,10]),
                session_rate=random.choice([200,250,300,350]),
                rating=rating, max_members=random.randint(15,30),
                bio=f'{fn} is a certified fitness coach with {exp} years of experience.',
            )
            c.specializations.set(random.sample(specs, random.randint(2,4)))
            coaches.append(c)

        # Certificates
        for coach in coaches:
            if not coach.certificates.exists():
                CoachCertificate.objects.create(
                    coach=coach, title='NASM Certified Personal Trainer',
                    issued_by='NASM', issue_date=date(2020,1,15),
                    expiry_date=date(2025,1,15),
                )

        # Attendance (last 30 days)
        for coach in coaches:
            for days_ago in range(30,0,-1):
                d = today - timedelta(days=days_ago)
                if not CoachAttendance.objects.filter(coach=coach,date=d).exists():
                    status = 'present' if random.random() > 0.1 else random.choice(['absent','late'])
                    CoachAttendance.objects.create(
                        coach=coach, date=d, status=status,
                        check_in=timezone.datetime(d.year,d.month,d.day,7,random.randint(0,30)).time(),
                        recorded_by=admin,
                    )

        # Schedule (next 14 days)
        for coach in coaches:
            for days_ahead in range(1,15):
                d = today + timedelta(days=days_ahead)
                for _ in range(random.randint(1,3)):
                    h = random.choice([7,8,9,10,16,17,18])
                    member = random.choice(members) if members else None
                    CoachSchedule.objects.create(
                        coach=coach,
                        session_type=random.choice(['pt','class','pt']),
                        title=random.choice(['PT Session','Morning HIIT','Strength Training','Cardio Blast']),
                        date=d, start_time=f'{h:02d}:00', end_time=f'{h+1:02d}:00',
                        member=member,
                    )

        # Salary (last 3 months)
        for coach in coaches:
            for i in range(1,4):
                m = today.replace(day=1) - timedelta(days=i*30)
                month_dt = m.replace(day=1)
                if not CoachSalary.objects.filter(coach=coach,month=month_dt).exists():
                    CoachSalary.objects.create(
                        coach=coach, month=month_dt,
                        base_salary=coach.base_salary,
                        bonus=random.choice([0,200,500]),
                        deductions=random.choice([0,100]),
                        commissions=random.randint(200,800),
                        status='paid', paid_date=month_dt + timedelta(days=28),
                        created_by=admin,
                    )

        self.stdout.write(self.style.SUCCESS(f'Done! {len(coaches)} coaches seeded.'))
