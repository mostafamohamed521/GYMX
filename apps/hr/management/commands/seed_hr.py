"""python manage.py seed_hr"""
import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from apps.hr.models import (Department, Position, Role, Employee, Shift,
                             ShiftAssignment, EmployeeAttendance, Payroll,
                             Bonus, LeaveRequest, PerformanceReview, Contract)

DEPTS = ['Operations','Sales','Front Desk','Maintenance','Management']
ROLES = ['Manager','Staff','Supervisor','Trainee']
EMPLOYEES = [
    ('Youssef','Ibrahim','youssef.ibrahim@gymx.com','01011112222','male',6000),
    ('Mariam','Adel','mariam.adel@gymx.com','01022223333','female',4500),
    ('Omar','Farouk','omar.farouk@gymx.com','01033334444','male',5200),
    ('Dina','Hassan','dina.hassan@gymx.com','01044445555','female',4000),
    ('Khaled','Mostafa','khaled.mostafa@gymx.com','01055556666','male',4800),
]

class Command(BaseCommand):
    help = 'Seed HR demo data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\nSeeding HR...\n'))
        today = date.today()

        depts = {}
        for name in DEPTS:
            d, _ = Department.objects.get_or_create(name=name)
            depts[name] = d

        roles = {}
        for name in ROLES:
            r, _ = Role.objects.get_or_create(name=name)
            roles[name] = r

        positions = {}
        for dept_name, dept in depts.items():
            p, _ = Position.objects.get_or_create(title=f'{dept_name} Staff', department=dept, defaults={'min_salary':3000,'max_salary':7000})
            positions[dept_name] = p

        shifts = []
        for name, st, et in [('Morning','06:00','14:00'),('Evening','14:00','22:00'),('Night','22:00','06:00')]:
            s, _ = Shift.objects.get_or_create(name=name, defaults={'start_time':st,'end_time':et})
            shifts.append(s)

        employees = []
        for fn, ln, email, phone, gender, salary in EMPLOYEES:
            dept_name = random.choice(DEPTS)
            emp, created = Employee.objects.get_or_create(email=email, defaults={
                'first_name':fn,'last_name':ln,'phone':phone,'gender':gender,
                'department':depts[dept_name],'position':positions[dept_name],
                'role':random.choice(list(roles.values())),
                'hire_date':today - timedelta(days=random.randint(60,800)),
                'base_salary':salary,'status':'active',
            })
            employees.append(emp)

            if created:
                # Shift assignment
                for day in random.sample(range(7), 5):
                    ShiftAssignment.objects.get_or_create(employee=emp, day_of_week=day, defaults={'shift': random.choice(shifts)})

                # Attendance last 30 days
                for days_ago in range(30,0,-1):
                    d = today - timedelta(days=days_ago)
                    status = 'present' if random.random() > 0.1 else random.choice(['absent','late'])
                    EmployeeAttendance.objects.get_or_create(employee=emp, date=d, defaults={'status':status})

                # Payroll last 3 months
                for i in range(1,4):
                    m = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
                    Payroll.objects.get_or_create(employee=emp, month=m, defaults={
                        'base_salary':salary,'bonuses':random.choice([0,200,500]),
                        'deductions':random.choice([0,100]),'status':'paid',
                        'paid_date':m+timedelta(days=28),
                    })

                # Contract
                Contract.objects.get_or_create(employee=emp, contract_type='Employment Contract', defaults={
                    'start_date':emp.hire_date,'salary':salary,'status':'active',
                })

                # Performance review
                PerformanceReview.objects.get_or_create(employee=emp, review_period='Q4 2025', defaults={
                    'rating':random.randint(3,5),
                    'strengths':'Reliable and punctual team member.',
                    'comments':'Good performance overall.',
                    'review_date':today - timedelta(days=30),
                })

        self.stdout.write(self.style.SUCCESS(f'Done! {len(employees)} employees, {Department.objects.count()} departments seeded.'))
