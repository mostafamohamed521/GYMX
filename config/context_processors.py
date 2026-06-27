from django.utils import timezone


def gymx_context(request):
    return {
        'today': timezone.now(),
        'app_name': 'GymX',
        'app_version': '1.0.0',
    }
