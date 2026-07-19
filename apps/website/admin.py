from django.contrib import admin
from .models import (BlogPost, Testimonial, FAQItem, JobOpening, JobApplication,
                      ContactMessage, GalleryImage, Event)

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title','status','published_at','views']
    prepopulated_fields = {'slug': ('title',)}

admin.site.register(Testimonial)
admin.site.register(FAQItem)
admin.site.register(JobOpening)
admin.site.register(JobApplication)
admin.site.register(ContactMessage)
admin.site.register(GalleryImage)
admin.site.register(Event)
