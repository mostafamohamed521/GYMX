from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import BlogPost, JobOpening


class StaticViewSitemap(Sitemap):
    """All the fixed public marketing pages (no per-object detail page)."""
    changefreq = 'weekly'

    # (url name, priority)
    pages = [
        ('website:home', 1.0),
        ('website:about', 0.8),
        ('website:locations', 0.8),
        ('website:services', 0.8),
        ('website:classes', 0.7),
        ('website:trainers', 0.7),
        ('website:timetable', 0.6),
        ('website:pricing', 0.9),
        ('website:plans', 0.9),
        ('website:offers', 0.8),
        ('website:equipment', 0.5),
        ('website:gift_cards', 0.5),
        ('website:group_plans', 0.5),
        ('website:gallery', 0.4),
        ('website:testimonials', 0.5),
        ('website:blog', 0.6),
        ('website:events', 0.5),
        ('website:faq', 0.5),
        ('website:contact', 0.7),
        ('website:careers', 0.5),
        ('website:privacy', 0.2),
        ('website:terms', 0.2),
    ]

    def items(self):
        return self.pages

    def location(self, item):
        return reverse(item[0])

    def priority(self, item):
        return item[1]


class BlogSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.6

    def items(self):
        return BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED)

    def lastmod(self, obj):
        return obj.published_at

    def location(self, obj):
        return reverse('website:blog_detail', args=[obj.slug])


class JobSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.4

    def items(self):
        return JobOpening.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.posted_at

    def location(self, obj):
        return reverse('website:job_apply', args=[obj.pk])
