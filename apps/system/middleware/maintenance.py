from django.shortcuts import render
from django.urls import reverse


class MaintenanceModeMiddleware:
    """Shows a maintenance page to non-admin users when maintenance mode is enabled.
    Admins/managers can still access everything (including turning maintenance mode back off).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from apps.system.models import MaintenanceSettings

        exempt_paths = ('/admin/', '/system/maintenance/', '/accounts/login/', '/static/', '/media/')
        if request.path.startswith(exempt_paths):
            return self.get_response(request)

        try:
            settings_obj = MaintenanceSettings.load()
        except Exception:
            return self.get_response(request)

        if settings_obj.is_enabled:
            user = getattr(request, 'user', None)
            is_admin = user and user.is_authenticated and (user.is_superuser or getattr(user, 'role', None) in ('super_admin', 'gym_manager'))
            if not is_admin:
                return render(request, 'system/maintenance_page.html', {'settings_obj': settings_obj}, status=503)

        return self.get_response(request)
