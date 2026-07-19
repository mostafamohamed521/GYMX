"""python manage.py seed_website"""
import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.website.models import BlogPost, Testimonial, FAQItem, JobOpening, Event
from apps.accounts.models import User

BLOG_POSTS = [
    ('5 Tips to Build Consistent Workout Habits', 'Small changes compound over time. Here is how to make the gym part of your routine.'),
    ('Why Protein Timing Matters', 'Understanding when to eat protein can maximize your muscle recovery and growth.'),
    ('The Truth About Cardio vs Weights', 'Both play a role — here is how to balance them for your goals.'),
]

FAQS = [
    ('general', 'What are your opening hours?', 'We are open daily from 6:00 AM to 11:00 PM, with reduced hours on Fridays.'),
    ('general', 'Do I need to book classes in advance?', 'Yes, we recommend booking through the member portal to guarantee your spot.'),
    ('membership', 'Can I freeze my membership?', 'Yes, you can submit a freeze request through the member portal for approval.'),
    ('membership', 'Is there a joining fee?', 'No joining fees — just choose your plan and get started.'),
    ('billing', 'What payment methods do you accept?', 'We accept cash, credit/debit cards, and digital wallets.'),
    ('classes', 'Are classes included in my membership?', 'Yes, all group classes are included with any active membership plan.'),
]

class Command(BaseCommand):
    help = 'Seed public website demo data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\nSeeding public website...\n'))
        admin = User.objects.filter(role='super_admin').first()
        today = date.today()

        for i, (title, excerpt) in enumerate(BLOG_POSTS):
            slug = title.lower().replace(' ', '-').replace(',', '').replace('?', '').replace("'","")
            BlogPost.objects.get_or_create(slug=slug, defaults={
                'title':title, 'excerpt':excerpt,
                'content':excerpt + '\n\n' + 'Consistency beats intensity. Focus on showing up, tracking progress, and celebrating small wins along the way. Our coaches are here to help you build a plan that fits your life.',
                'author':admin, 'status':'published',
                'published_at':timezone.now()-timedelta(days=i*5),
            })

        testimonials_data = [
            ('Mona Farouk','Member since 2022','GymX completely changed how I approach fitness. The coaches actually care about your progress.',5),
            ('Karim Adel','Member since 2023','Best equipment in Mansoura, hands down. Clean, modern, and always available.',5),
            ('Yasmine Tarek','Member since 2021','The nutrition coaching helped me lose 15kg in 6 months. Forever grateful!',5),
        ]
        for name, role, quote, rating in testimonials_data:
            Testimonial.objects.get_or_create(name=name, defaults={'role':role,'quote':quote,'rating':rating})

        for cat, q, a in FAQS:
            FAQItem.objects.get_or_create(question=q, defaults={'answer':a,'category':cat})

        JobOpening.objects.get_or_create(title='Personal Trainer', defaults={
            'department':'Fitness','job_type':'full_time',
            'description':'We are looking for a certified personal trainer to join our growing team.',
            'requirements':'- Certified PT qualification\n- 2+ years experience\n- Passion for client success',
        })
        JobOpening.objects.get_or_create(title='Front Desk Receptionist', defaults={
            'department':'Operations','job_type':'part_time',
            'description':'Join our front desk team providing excellent member service.',
            'requirements':'- Strong communication skills\n- Customer service experience preferred',
        })

        Event.objects.get_or_create(title='Summer Fitness Challenge Kickoff', defaults={
            'description':'Join us for the launch of our 8-week summer transformation challenge with prizes!',
            'date':today+timedelta(days=14), 'start_time':'09:00', 'location':'Main Branch',
        })
        Event.objects.get_or_create(title='Free Community Yoga Session', defaults={
            'description':'A free open yoga session for members and the community.',
            'date':today+timedelta(days=5), 'start_time':'08:00', 'location':'Studio A',
        })

        self.stdout.write(self.style.SUCCESS('Done! Blog posts, testimonials, FAQs, jobs, and events seeded.'))
