"""python manage.py seed_branches"""
import random
from apps.branches.models import Branch, BranchSettings
from apps.members.models import Member
from apps.hr.models import Employee
from apps.accounts.models import User
from django.core.management.base import BaseCommand

BRANCHES = [
    ('GymX — Mansoura Main','Mansoura','123 El Gomhoria St', True),
    ('GymX — Talkha','Talkha','45 Nile Corniche', False),
    ('GymX — Mit Ghamr','Mit Ghamr','8 El Tahrir Square', False),
]

class Command(BaseCommand):
    help = 'Seed branch demo data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\nSeeding branches...\n'))
        manager = User.objects.filter(role='gym_manager').first()

        branches = []
        for name, city, address, is_main in BRANCHES:
            b, created = Branch.objects.get_or_create(name=name, defaults={
                'city':city, 'address':address, 'is_main_branch':is_main,
                'manager':manager, 'status':'active', 'phone':'01000000000',
                'max_capacity':random.choice([150,200,300]),
            })
            if created:
                BranchSettings.objects.get_or_create(branch=b)
            branches.append(b)

        # Assign existing members/employees to branches
        members = list(Member.objects.all())
        for m in members:
            if not m.branch:
                m.branch = random.choice(branches)
                m.save(update_fields=['branch'])

        employees = list(Employee.objects.all())
        for e in employees:
            if not e.branch:
                e.branch = random.choice(branches)
                e.save(update_fields=['branch'])

        self.stdout.write(self.style.SUCCESS(f'Done! {len(branches)} branches seeded, {len(members)} members and {len(employees)} employees assigned.'))
