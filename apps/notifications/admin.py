from django.contrib import admin
from .models import EmailTemplate, SMSTemplate, PushNotification, Announcement, ScheduledMessage

admin.site.register(EmailTemplate)
admin.site.register(SMSTemplate)
admin.site.register(PushNotification)
admin.site.register(Announcement)
admin.site.register(ScheduledMessage)
