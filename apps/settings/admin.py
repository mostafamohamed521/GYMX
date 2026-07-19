from django.contrib import admin
from .models import SystemSettings, BusinessHours, Holiday, AuditLog, BackupRecord

admin.site.register(SystemSettings)
admin.site.register(BusinessHours)
admin.site.register(Holiday)
admin.site.register(AuditLog)
admin.site.register(BackupRecord)
