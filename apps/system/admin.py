from django.contrib import admin
from .models import MaintenanceSettings, ReleaseNote, HelpArticle, DocPage

admin.site.register(MaintenanceSettings)
admin.site.register(ReleaseNote)
admin.site.register(HelpArticle)
admin.site.register(DocPage)
