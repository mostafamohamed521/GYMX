from django.utils import timezone


def gymx_context(request):
    context = {
        'today': timezone.now(),
        'app_name': 'GymX',
        'app_version': '1.0.0',
    }
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        role = getattr(user, 'role', None)
        context.update({
            'is_admin_role':       user.is_superuser or role in ('super_admin', 'gym_manager'),
            'is_front_desk_role':  user.is_superuser or role in ('super_admin', 'gym_manager', 'receptionist'),
            'is_coach_role':       role == 'coach',
            'is_member_role':      role == 'member',
        })
    return context
