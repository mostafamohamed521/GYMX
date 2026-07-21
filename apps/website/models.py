from django.db import models
from django.utils import timezone
from apps.accounts.models import User
from apps.accounts.validators import validate_document_file


class BlogPost(models.Model):
    class Status(models.TextChoices):
        DRAFT     = 'draft',     'Draft'
        PUBLISHED = 'published', 'Published'

    title       = models.CharField(max_length=200)
    slug        = models.SlugField(max_length=220, unique=True)
    excerpt     = models.CharField(max_length=300, blank=True)
    content     = models.TextField()
    cover_image = models.ImageField(upload_to='blog/', null=True, blank=True)
    author      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status      = models.CharField(max_length=10, choices=Status.choices, default=Status.PUBLISHED)
    published_at= models.DateTimeField(default=timezone.now)
    views       = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'website_blog_posts'
        ordering = ['-published_at']

    def __str__(self):
        return self.title


class Testimonial(models.Model):
    name        = models.CharField(max_length=150)
    role        = models.CharField(max_length=150, blank=True, help_text='e.g. Member since 2022')
    photo       = models.ImageField(upload_to='testimonials/', null=True, blank=True)
    quote       = models.TextField()
    rating      = models.PositiveIntegerField(default=5)
    is_featured = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'website_testimonials'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class FAQItem(models.Model):
    class Category(models.TextChoices):
        GENERAL     = 'general',     'General'
        MEMBERSHIP  = 'membership',  'Membership'
        BILLING     = 'billing',     'Billing'
        CLASSES     = 'classes',     'Classes'

    question    = models.CharField(max_length=255)
    answer      = models.TextField()
    category    = models.CharField(max_length=12, choices=Category.choices, default=Category.GENERAL)
    order       = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'website_faq'
        ordering = ['category', 'order']

    def __str__(self):
        return self.question


class JobOpening(models.Model):
    class Type(models.TextChoices):
        FULL_TIME = 'full_time', 'Full-time'
        PART_TIME = 'part_time', 'Part-time'
        CONTRACT  = 'contract',  'Contract'

    title       = models.CharField(max_length=150)
    department  = models.CharField(max_length=100, blank=True)
    location    = models.CharField(max_length=150, default='Mansoura, Egypt')
    job_type    = models.CharField(max_length=10, choices=Type.choices, default=Type.FULL_TIME)
    description = models.TextField()
    requirements= models.TextField(blank=True)
    is_active   = models.BooleanField(default=True)
    posted_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'website_job_openings'
        ordering = ['-posted_at']

    def __str__(self):
        return self.title


class JobApplication(models.Model):
    job         = models.ForeignKey(JobOpening, on_delete=models.CASCADE, related_name='applications')
    full_name   = models.CharField(max_length=150)
    email       = models.EmailField()
    phone       = models.CharField(max_length=20, blank=True)
    resume      = models.FileField(upload_to='applications/', null=True, blank=True,
                                   validators=[validate_document_file])
    cover_letter= models.TextField(blank=True)
    submitted_at= models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'website_job_applications'
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.full_name} — {self.job.title}"


class ContactMessage(models.Model):
    name        = models.CharField(max_length=150)
    email       = models.EmailField()
    phone       = models.CharField(max_length=20, blank=True)
    subject     = models.CharField(max_length=200, blank=True)
    message     = models.TextField()
    is_read     = models.BooleanField(default=False)
    submitted_at= models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'website_contact_messages'
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.name} — {self.subject}"


class GalleryImage(models.Model):
    class Category(models.TextChoices):
        FACILITY  = 'facility',  'Facility'
        CLASSES   = 'classes',   'Classes'
        EVENTS    = 'events',    'Events'
        TRAINERS  = 'trainers',  'Trainers'

    title       = models.CharField(max_length=150, blank=True)
    image       = models.ImageField(upload_to='gallery/')
    category    = models.CharField(max_length=10, choices=Category.choices, default=Category.FACILITY)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'website_gallery'
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title or f"Image #{self.pk}"


class Event(models.Model):
    title       = models.CharField(max_length=200)
    description = models.TextField()
    date        = models.DateField()
    start_time  = models.TimeField()
    location    = models.CharField(max_length=200, blank=True)
    cover_image = models.ImageField(upload_to='events/', null=True, blank=True)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'website_events'
        ordering = ['date']

    def __str__(self):
        return self.title

    @property
    def is_upcoming(self):
        return self.date >= timezone.now().date()
