from django.urls import path
from . import views

app_name = 'coresystem'

urlpatterns = [
    # Error page previews (for design/QA purposes)
    path('errors/401/',                   views.preview_401,          name='preview_401'),
    path('errors/403/',                   views.preview_403,          name='preview_403'),
    path('errors/404/',                   views.preview_404,          name='preview_404'),
    path('errors/500/',                   views.preview_500,          name='preview_500'),

    path('maintenance/',                  views.maintenance_mode,     name='maintenance'),
    path('status/',                       views.system_status,        name='status'),
    path('help/',                         views.help_center,          name='help'),
    path('docs/',                         views.documentation,        name='docs'),
    path('release-notes/',                views.release_notes,        name='release_notes'),
    path('version-history/',              views.version_history,      name='version_history'),
]
