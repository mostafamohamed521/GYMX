from django.contrib import admin
from .models import SavedReport, ExportLog

admin.site.register(SavedReport)
admin.site.register(ExportLog)
