from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.core.exceptions import ValidationError

from .models import (
    BlogPost, Testimonial, FAQItem, JobOpening, JobApplication,
    ContactMessage, GalleryImage, Event,
)
from apps.accounts.validators import validate_document_file
from apps.memberships.models import MembershipPlan
from apps.coaches.models import Coach
from apps.classes.models import GymClass, ClassSchedule
from .rate_limit import rate_limit_post


# ── 1. Home ─────────────────────────────────────────────────
def home(request):
    plans = MembershipPlan.objects.filter(is_active=True)[:3]
    trainers = Coach.objects.filter(status='active').order_by('-rating')[:4]
    testimonials = Testimonial.objects.filter(is_featured=True)[:6]
    classes = GymClass.objects.filter(is_active=True)[:6] if hasattr(GymClass, 'is_active') else GymClass.objects.all()[:6]
    latest_posts = BlogPost.objects.filter(status='published')[:3]
    return render(request, 'website/home.html', {
        'plans': plans, 'trainers': trainers, 'testimonials': testimonials,
        'classes': classes, 'latest_posts': latest_posts,
    })


# ── 2. About Us ─────────────────────────────────────────────
def about_us(request):
    trainers = Coach.objects.filter(status='active').order_by('-rating')[:4]
    return render(request, 'website/about.html', {'trainers': trainers, 'trainers_count': trainers.count()})


# ── 2b. Locations ───────────────────────────────────────────
def locations(request):
    from apps.branches.models import Branch
    branches = Branch.objects.exclude(status='closed').order_by('-is_main_branch', 'name')
    return render(request, 'website/locations.html', {'branches': branches})


# ── 2c. Offers & Promotions ───────────────────────────────────
def offers(request):
    from django.utils import timezone
    from apps.memberships.models import Offer
    today = timezone.now().date()
    live_offers = (
        Offer.objects
        .filter(is_active=True, valid_from__lte=today, valid_until__gte=today)
        .select_related('discount')
        .prefetch_related('applicable_plans')
        .order_by('-is_featured', 'valid_until')
    )
    return render(request, 'website/offers.html', {'offers': live_offers})


# ── 2d. Equipment Showcase ─────────────────────────────────────
def equipment(request):
    from apps.inventory.models import Equipment, ProductCategory
    # Only "operational" gear is shown — maintenance/broken/retired status,
    # serial numbers, purchase price, and location are internal ops data
    # and never appear on the public page.
    items = (
        Equipment.objects
        .filter(status='operational')
        .select_related('category', 'brand')
        .order_by('category__name', 'name')
    )
    categories = ProductCategory.objects.filter(equipment__status='operational').distinct()
    return render(request, 'website/equipment.html', {'items': items, 'categories': categories})


# ── 2e. Gift Cards ──────────────────────────────────────────────
@rate_limit_post('gift_cards', max_attempts=5, window_seconds=3600)
def gift_cards(request):
    from apps.crm.models import Lead
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        amount = request.POST.get('amount', '').strip()
        if first_name and phone:
            Lead.objects.create(
                first_name=first_name, last_name=last_name or '-', phone=phone, email=email,
                source=Lead.Source.WEBSITE,
                interest=f'Gift card request — {amount} EGP' if amount else 'Gift card request',
                notes=f'Submitted via the public Gift Cards page. Requested amount: {amount or "unspecified"} EGP.',
            )
            messages.success(request, "Request received! Our team will call you shortly to confirm the details.")
        else:
            messages.error(request, 'Please enter your name and phone number.')
        return redirect('website:gift_cards')
    return render(request, 'website/gift_cards.html', {})


# ── 2f. Corporate & Family Plans ────────────────────────────────
@rate_limit_post('group_plans', max_attempts=5, window_seconds=3600)
def group_plans(request):
    from apps.crm.models import Lead
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        plan_type = request.POST.get('plan_type', 'Group')
        company = request.POST.get('company', '').strip()
        if first_name and phone:
            Lead.objects.create(
                first_name=first_name, last_name=last_name or '-', phone=phone, email=email,
                source=Lead.Source.WEBSITE,
                interest=f'{plan_type} plan inquiry' + (f' — {company}' if company else ''),
                notes=f'Submitted via the public Group Plans page.' + (f' Company: {company}.' if company else ''),
            )
            messages.success(request, "Thanks! Our team will reach out to set up your plan.")
        else:
            messages.error(request, 'Please enter your name and phone number.')
        return redirect('website:group_plans')
    return render(request, 'website/group_plans.html', {})


# ── 3. Services ─────────────────────────────────────────────
def services(request):
    classes = GymClass.objects.all()[:8]
    return render(request, 'website/services.html', {'classes': classes})


# ── 4. Membership Plans ──────────────────────────────────────
def membership_plans(request):
    plans = MembershipPlan.objects.filter(is_active=True)
    return render(request, 'website/plans.html', {'plans': plans})


# ── 5. Trainers ───────────────────────────────────────────────
def trainers(request):
    trainer_list = Coach.objects.filter(status='active').order_by('-rating')
    return render(request, 'website/trainers.html', {'trainer_list': trainer_list})


def trainer_detail(request, pk):
    from django.shortcuts import get_object_or_404
    # Only ever query active coaches, and the template only ever displays
    # public-safe fields (name/bio/photo/specializations/certs/rating) —
    # salary, commission_rate, session_rate, national_id, address, and
    # phone_secondary are never passed to or rendered by this page.
    coach = get_object_or_404(
        Coach.objects.prefetch_related('specializations', 'certificates'),
        pk=pk, status='active'
    )
    return render(request, 'website/trainer_detail.html', {'coach': coach})


# ── 6. Classes ─────────────────────────────────────────────────
def classes(request):
    class_list = GymClass.objects.all()
    return render(request, 'website/classes.html', {'class_list': class_list})


# ── 7. Timetable ───────────────────────────────────────────────
def timetable(request):
    schedules = ClassSchedule.objects.select_related('gym_class').order_by('day_of_week', 'start_time') if hasattr(ClassSchedule, 'day_of_week') else ClassSchedule.objects.select_related('gym_class').all()
    days = ClassSchedule.DAYS if hasattr(ClassSchedule, 'DAYS') else []

    by_day = {d[0]: [] for d in days}
    for s in schedules:
        day_val = getattr(s, 'day_of_week', getattr(s, 'day', None))
        if day_val in by_day:
            by_day[day_val].append(s)

    grid = [{'day_label': label, 'sessions': by_day.get(val, [])} for val, label in days]
    return render(request, 'website/timetable.html', {'grid': grid})


# ── 8. Gallery ─────────────────────────────────────────────────
def gallery(request):
    category = request.GET.get('category', '')
    images = GalleryImage.objects.all()
    if category:
        images = images.filter(category=category)
    return render(request, 'website/gallery.html', {
        'images': images, 'categories': GalleryImage.Category.choices, 'category': category,
    })


# ── 9. Testimonials ───────────────────────────────────────────
def testimonials(request):
    testimonial_list = Testimonial.objects.all()
    return render(request, 'website/testimonials.html', {'testimonial_list': testimonial_list})


# ── 10. Pricing ────────────────────────────────────────────────
def pricing(request):
    plans = MembershipPlan.objects.filter(is_active=True)
    return render(request, 'website/pricing.html', {'plans': plans})


# ── 11. Blog ───────────────────────────────────────────────────
def blog(request):
    posts = BlogPost.objects.filter(status='published')
    return render(request, 'website/blog.html', {'posts': posts})


# ── 12. Blog Details ────────────────────────────────────────────
def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, status='published')
    post.views += 1
    post.save(update_fields=['views'])
    related = BlogPost.objects.filter(status='published').exclude(pk=post.pk)[:3]
    return render(request, 'website/blog_detail.html', {'post': post, 'related': related})


# ── 13. Events ─────────────────────────────────────────────────
def events(request):
    today = timezone.now().date()
    upcoming = Event.objects.filter(is_active=True, date__gte=today)
    past = Event.objects.filter(is_active=True, date__lt=today)
    return render(request, 'website/events.html', {'upcoming': upcoming, 'past': past})


# ── 14. FAQ ─────────────────────────────────────────────────────
def faq(request):
    faqs = FAQItem.objects.all()
    grouped = {}
    for f in faqs:
        grouped.setdefault(f.category, []).append(f)
    return render(request, 'website/faq.html', {'grouped': grouped})


# ── 15. Contact Us ──────────────────────────────────────────────
@rate_limit_post('contact', max_attempts=8, window_seconds=3600)
def contact_us(request):
    if request.method == 'POST':
        ContactMessage.objects.create(
            name=request.POST.get('name'), email=request.POST.get('email'),
            phone=request.POST.get('phone', ''), subject=request.POST.get('subject', ''),
            message=request.POST.get('message'),
        )
        messages.success(request, "Thanks! We've received your message and will get back to you soon.")
        return redirect('website:contact')
    return render(request, 'website/contact.html', {})


# ── 16. Careers ───────────────────────────────────────────────
def careers(request):
    jobs = JobOpening.objects.filter(is_active=True)
    return render(request, 'website/careers.html', {'jobs': jobs})


@rate_limit_post('job_apply', max_attempts=5, window_seconds=3600)
def job_apply(request, pk):
    job = get_object_or_404(JobOpening, pk=pk, is_active=True)
    if request.method == 'POST':
        resume_file = request.FILES.get('resume')
        if resume_file:
            try:
                validate_document_file(resume_file)
            except ValidationError as e:
                messages.error(request, e.messages[0])
                return render(request, 'website/job_apply.html', {'job': job})

        JobApplication.objects.create(
            job=job, full_name=request.POST.get('full_name'), email=request.POST.get('email'),
            phone=request.POST.get('phone', ''), cover_letter=request.POST.get('cover_letter', ''),
            resume=resume_file,
        )
        messages.success(request, f'Application submitted for {job.title}! We will contact you soon.')
        return redirect('website:careers')
    return render(request, 'website/job_apply.html', {'job': job})


# ── 17. Privacy Policy ────────────────────────────────────────
def privacy_policy(request):
    return render(request, 'website/privacy.html', {})


# ── 18. Terms & Conditions ─────────────────────────────────────
def terms_conditions(request):
    return render(request, 'website/terms.html', {})
