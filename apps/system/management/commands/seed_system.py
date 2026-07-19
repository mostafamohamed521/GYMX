"""python manage.py seed_system"""
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from apps.system.models import ReleaseNote, HelpArticle, DocPage

class Command(BaseCommand):
    help = 'Seed system app demo data (release notes, help articles, docs)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\nSeeding system data...\n'))
        today = date.today()

        releases = [
            ('1.0.0', 'Initial Release', 'major', 'The first public release of GymX.', [
                'Member management, memberships, attendance, and payments',
                'Coach and workout tracking',
                'POS and inventory management',
            ], today - timedelta(days=180)),
            ('1.5.0', 'CRM & Branch Expansion', 'minor', 'Added multi-branch support and CRM tools.', [
                'Branch management with transfers',
                'CRM: leads, follow-ups, loyalty program',
                'Reports & analytics dashboard',
            ], today - timedelta(days=90)),
            ('2.0.0', 'AI & Public Website', 'major', 'Major release adding AI-powered features and the public website.', [
                'AI workout generator and nutrition advisor',
                'Member churn prediction and revenue forecasting',
                'Full public marketing website',
                'Member self-service portal',
            ], today - timedelta(days=10)),
        ]
        for version, title, rtype, summary, changes, released_at in releases:
            ReleaseNote.objects.get_or_create(version=version, defaults={
                'title':title, 'release_type':rtype, 'summary':summary,
                'changes':changes, 'released_at':released_at,
            })

        help_articles = [
            ('getting_started', 'How to add a new member', 'Go to Members → Add Member, fill in the required details, and assign a membership plan.'),
            ('getting_started', 'How to check in a member', 'Use Attendance → Live Check-in, search by name or scan their QR code.'),
            ('payments', 'How to record a payment', 'Go to Payments → New Payment, select the member and payment method.'),
            ('reports', 'How to export a report', 'Visit Reports → Export Center to generate PDF or Excel exports.'),
            ('troubleshooting', 'A member cannot log in to the portal', 'Verify their account is linked to a Member profile via Accounts, then reset their password if needed.'),
        ]
        for cat, title, content in help_articles:
            HelpArticle.objects.get_or_create(title=title, defaults={'category':cat,'content':content})

        doc_pages = [
            ('overview', 'System Architecture', 'GymX is built on Django 5 with a modular app-per-domain structure (members, payments, workouts, etc.), role-based access control, and a shared design system.'),
            ('modules', 'Role-Based Permissions', 'Access is controlled via apps.accounts.permissions.role_required, restricting views by role group: ADMIN_ROLES, FRONT_DESK_ROLES, STAFF_ROLES, COACH_ROLES.'),
            ('admin', 'Running Seed Commands', 'Each app includes a `seed_<app>` management command to populate demo data. Run them after migrations in dependency order.'),
        ]
        for section, title, content in doc_pages:
            DocPage.objects.get_or_create(title=title, defaults={'section':section,'content':content})

        self.stdout.write(self.style.SUCCESS('Done! Release notes, help articles, and docs seeded.'))
