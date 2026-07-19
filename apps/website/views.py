from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q

from .models import (
    BlogPost, Testimonial, FAQItem, JobOpening, JobApplication,
    ContactMessage, GalleryImage, Event,
)
from apps.memberships.models import MembershipPlan
from apps.coaches.models import Coach
from apps.classes.models import GymClass, ClassSchedule


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
    trainers_count = Coach.objects.filter(status='active').count()
    return render(request, 'website/about.html', {'trainers_count': trainers_count})


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


def job_apply(request, pk):
    job = get_object_or_404(JobOpening, pk=pk, is_active=True)
    if request.method == 'POST':
        JobApplication.objects.create(
            job=job, full_name=request.POST.get('full_name'), email=request.POST.get('email'),
            phone=request.POST.get('phone', ''), cover_letter=request.POST.get('cover_letter', ''),
            resume=request.FILES.get('resume'),
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
