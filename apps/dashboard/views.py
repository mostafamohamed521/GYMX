from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

User = get_user_model()


@login_required
def index_view(request):
    # Placeholder stats — will be replaced with real data in future sprints
    stats = {
        'total_members': 248,
        'active_members': 193,
        'total_coaches': 12,
        'monthly_revenue': 18450,
        'new_members_this_month': 34,
        'attendance_today': 67,
        'active_memberships': 185,
        'pending_payments': 8,
    }

    # Recent activity placeholder
    recent_activity = [
        {'icon': 'user-plus', 'color': 'success', 'text': 'New member registered: John Smith', 'time': '2 min ago'},
        {'icon': 'credit-card', 'color': 'primary', 'text': 'Payment received: $120 from Sarah Connor', 'time': '15 min ago'},
        {'icon': 'calendar-check', 'color': 'info', 'text': 'Class scheduled: Morning Yoga at 7:00 AM', 'time': '1 hour ago'},
        {'icon': 'user-minus', 'color': 'warning', 'text': 'Membership expired: Mike Johnson', 'time': '3 hours ago'},
        {'icon': 'dumbbell', 'color': 'secondary', 'text': 'Coach Ahmed updated training plans', 'time': '5 hours ago'},
    ]

    # Top coaches placeholder
    top_coaches = [
        {'name': 'Ahmed Hassan', 'specialty': 'CrossFit', 'members': 24, 'rating': 4.9},
        {'name': 'Sara Mostafa', 'specialty': 'Yoga & Pilates', 'members': 18, 'rating': 4.8},
        {'name': 'Omar Khalil', 'specialty': 'Powerlifting', 'members': 21, 'rating': 4.7},
        {'name': 'Nour Adel', 'specialty': 'Cardio', 'members': 16, 'rating': 4.6},
    ]

    context = {
        'stats': stats,
        'recent_activity': recent_activity,
        'top_coaches': top_coaches,
        'page_title': 'Dashboard',
    }
    return render(request, 'dashboard/index.html', context)
