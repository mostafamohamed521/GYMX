from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect, render
from django.contrib.sitemaps.views import sitemap
from apps.website.sitemaps import StaticViewSitemap, BlogSitemap, JobSitemap

def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    return redirect('website:home')

def robots_txt(request):
    return render(request, 'robots.txt', content_type='text/plain')

sitemaps = {
    'static': StaticViewSitemap,
    'blog': BlogSitemap,
    'jobs': JobSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('', root_redirect),
    path('auth/', include('apps.accounts.urls', namespace='accounts')),
    path('dashboard/', include('apps.dashboard.urls', namespace='dashboard')),
    path('members/',       include('apps.members.urls',       namespace='members')),
    path('memberships/',   include('apps.memberships.urls', namespace='memberships')),
    path('attendance/',    include('apps.attendance.urls',    namespace='attendance')),
    path('payments/',      include('apps.payments.urls',      namespace='payments')),
    path('coaches/',       include('apps.coaches.urls',       namespace='coaches')),
    path('workouts/',      include('apps.workouts.urls',      namespace='workouts')),
    path('nutrition/',     include('apps.nutrition.urls',     namespace='nutrition')),
    path('classes/',       include('apps.classes.urls',       namespace='classes')),
    path('hr/',            include('apps.hr.urls',             namespace='hr')),
    path('inventory/',     include('apps.inventory.urls',     namespace='inventory')),
    path('pos/',           include('apps.pos.urls',           namespace='pos')),
    path('branches/',      include('apps.branches.urls',      namespace='branches')),
    path('crm/',           include('apps.crm.urls',           namespace='crm')),
    path('reports/',       include('apps.reports.urls',       namespace='reports')),
    path('notifications/', include('apps.notifications.urls', namespace='notifications')),
    path('finance/',       include('apps.finance.urls',       namespace='finance')),
    path('settings/',      include('apps.settings.urls',      namespace='gymsettings')),
    path('portal/',        include('apps.portal.urls',        namespace='portal')),
    path('site/',          include('apps.website.urls',       namespace='website')),
    path('ai/',            include('apps.aifeatures.urls',    namespace='aifeatures')),
    path('system/',        include('apps.system.urls',        namespace='coresystem')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error page handlers (only take effect when DEBUG=False)
handler403 = 'apps.system.views.custom_403'
handler404 = 'apps.system.views.custom_404'
handler500 = 'apps.system.views.custom_500'
