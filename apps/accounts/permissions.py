"""
Central role-based access control for GymX.

Roles (from apps.accounts.models.User.Role):
    super_admin   — full access to everything
    gym_manager   — full operational access (no system/security settings)
    receptionist  — front-desk: members, memberships, attendance, payments (view/add only)
    coach         — only their own assigned members, schedule, classes, workouts
    member        — only their own portal data (membership, payments, attendance, workouts...)

Usage:
    from apps.accounts.permissions import role_required

    @role_required('super_admin', 'gym_manager')
    def some_admin_view(request):
        ...

    @role_required('super_admin', 'gym_manager', 'receptionist')
    def front_desk_view(request):
        ...
"""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse


# Role groups used across the app — keep these as the single source of truth.
ADMIN_ROLES       = ('super_admin', 'gym_manager')
FRONT_DESK_ROLES  = ('super_admin', 'gym_manager', 'receptionist')
STAFF_ROLES       = ('super_admin', 'gym_manager', 'receptionist', 'coach')
COACH_ROLES       = ('super_admin', 'gym_manager', 'coach')
ALL_ROLES         = ('super_admin', 'gym_manager', 'receptionist', 'coach', 'member')


def _is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'ajax' in request.path


def role_required(*roles):
    """Restrict a view to the given roles. Superusers always pass.
    Redirects (with a message) to the dashboard if the role doesn't match,
    rather than raising a hard 403, so the person lands somewhere useful.
    AJAX requests get a JSON 403 instead of a redirect.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if user.is_superuser or user.role in roles:
                return view_func(request, *args, **kwargs)
            if _is_ajax(request):
                return JsonResponse({'status': 'error', 'message': 'Permission denied.'}, status=403)
            messages.error(request, "You don't have permission to access that page.")
            return redirect('dashboard:index')
        return _wrapped
    return decorator


def owner_or_role_required(get_owner_user_id, *roles):
    """For pages showing a specific person's data (e.g. a coach's own profile,
    a member's own portal). Staff in `roles` can view anyone's; otherwise the
    logged-in user must be the owner, matched via `get_owner_user_id(request, **kwargs)`.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if user.is_superuser or user.role in roles:
                return view_func(request, *args, **kwargs)
            owner_id = get_owner_user_id(request, **kwargs)
            if owner_id is not None and owner_id == user.pk:
                return view_func(request, *args, **kwargs)
            messages.error(request, "You can only view your own information.")
            return redirect('dashboard:index')
        return _wrapped
    return decorator


def in_group(user, *roles):
    """Plain helper for use in templates/views without redirect side-effects."""
    return user.is_authenticated and (user.is_superuser or user.role in roles)
