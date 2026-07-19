import random
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Count, Avg
from django.http import JsonResponse

from apps.accounts.permissions import role_required, ADMIN_ROLES, ALL_ROLES
from .models import ChatConversation, ChatMessage, GeneratedWorkoutPlan, GeneratedNutritionAdvice
from apps.members.models import Member
from apps.memberships.models import MemberSubscription
from apps.attendance.models import AttendanceRecord
from apps.payments.models import Payment
from apps.workouts.models import Exercise
from apps.pos.models import Sale


# ── 1. AI Dashboard ────────────────────────────────────────
@role_required(*ADMIN_ROLES)
def ai_dashboard(request):
    today = date.today()
    active_members = Member.objects.filter(status='active').count()
    at_risk = _compute_churn_scores()
    high_risk_count = sum(1 for c in at_risk if c['risk_level'] == 'High')

    revenue_data = _forecast_revenue()
    attendance_data = _forecast_attendance()

    return render(request, 'aifeatures/ai_dashboard.html', {
        'active_members': active_members, 'high_risk_count': high_risk_count,
        'next_month_forecast': revenue_data['forecast'][0] if revenue_data['forecast'] else 0,
        'next_week_attendance': attendance_data['forecast'][0] if attendance_data['forecast'] else 0,
    })


# ── 2. AI Workout Generator ────────────────────────────────
@role_required(*ADMIN_ROLES)
def workout_generator(request):
    members = Member.objects.filter(status='active').order_by('first_name')
    generated = None

    if request.method == 'POST':
        member = get_object_or_404(Member, pk=request.POST.get('member'))
        goal = request.POST.get('goal', 'general_fit')
        level = request.POST.get('level', 'beginner')
        days = int(request.POST.get('days_per_week', 3))

        plan = _generate_workout_plan(goal, level, days)
        GeneratedWorkoutPlan.objects.create(
            member=member, goal=goal, level=level, days_per_week=days, generated_plan=plan,
        )
        generated = plan
        messages.success(request, f'AI workout plan generated for {member.get_full_name()}!')

    recent_plans = GeneratedWorkoutPlan.objects.select_related('member').order_by('-created_at')[:5]
    return render(request, 'aifeatures/workout_generator.html', {
        'members': members, 'generated': generated, 'recent_plans': recent_plans,
        'goals': GeneratedWorkoutPlan.Goal.choices, 'levels': GeneratedWorkoutPlan.Level.choices,
    })


def _generate_workout_plan(goal, level, days_per_week):
    """Rule-based workout plan generator using the exercise library."""
    goal_split = {
        'weight_loss': ['cardio', 'full_body', 'core'],
        'muscle_gain': ['chest', 'back', 'legs', 'shoulders', 'arms'],
        'endurance':   ['cardio', 'legs', 'core'],
        'general_fit': ['full_body', 'core', 'cardio'],
    }
    focus_areas = goal_split.get(goal, ['full_body'])
    sets_reps = {'beginner': '3x10', 'intermediate': '4x10', 'advanced': '5x8'}.get(level, '3x10')

    day_plans = []
    exercises_qs = list(Exercise.objects.all()[:40])
    for d in range(1, days_per_week + 1):
        focus = focus_areas[(d - 1) % len(focus_areas)]
        matched = [e.name for e in exercises_qs if focus in e.muscle_group.lower()] if exercises_qs else []
        if not matched:
            matched = [e.name for e in random.sample(exercises_qs, min(4, len(exercises_qs)))] if exercises_qs else [
                'Bodyweight Squats', 'Push-ups', 'Plank', 'Jumping Jacks'
            ]
        day_plans.append({
            'day': d, 'focus': focus.replace('_', ' ').title(),
            'exercises': matched[:5], 'sets_reps': sets_reps,
        })
    return {'goal': goal, 'level': level, 'days_per_week': days_per_week, 'schedule': day_plans}


# ── 3. AI Nutrition Advisor ────────────────────────────────
@role_required(*ADMIN_ROLES)
def nutrition_advisor(request):
    members = Member.objects.filter(status='active').order_by('first_name')
    result = None

    if request.method == 'POST':
        member = get_object_or_404(Member, pk=request.POST.get('member'))
        weight = float(request.POST.get('weight_kg'))
        height = float(request.POST.get('height_cm'))
        age = int(request.POST.get('age'))
        gender = request.POST.get('gender', 'male')
        activity = request.POST.get('activity_level', 'moderate')
        goal = request.POST.get('goal', 'maintain')

        # Mifflin-St Jeor equation
        if gender == 'male':
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161

        activity_multipliers = {'sedentary': 1.2, 'light': 1.375, 'moderate': 1.55, 'active': 1.725, 'very_active': 1.9}
        tdee = bmr * activity_multipliers.get(activity, 1.55)

        goal_adjustment = {'lose': -500, 'maintain': 0, 'gain': 300}
        recommended = tdee + goal_adjustment.get(goal, 0)

        protein_g = weight * 2.0
        fat_g = (recommended * 0.25) / 9
        carbs_g = (recommended - (protein_g * 4) - (fat_g * 9)) / 4

        advice = GeneratedNutritionAdvice.objects.create(
            member=member, weight_kg=weight, height_cm=height, age=age, gender=gender,
            activity_level=activity, goal=goal, bmr=round(bmr), tdee=round(tdee),
            recommended_calories=round(recommended), protein_g=round(protein_g),
            carbs_g=round(carbs_g), fat_g=round(fat_g),
        )
        result = advice

    recent = GeneratedNutritionAdvice.objects.select_related('member').order_by('-created_at')[:5]
    return render(request, 'aifeatures/nutrition_advisor.html', {
        'members': members, 'result': result, 'recent': recent,
    })


# ── 4. AI Chat Assistant ────────────────────────────────────
@role_required(*ADMIN_ROLES)
def chat_assistant(request):
    conversation, _ = ChatConversation.objects.get_or_create(user=request.user, defaults={'title': 'Assistant Chat'})
    conv_messages = conversation.messages.order_by('created_at')
    return render(request, 'aifeatures/chat_assistant.html', {
        'conversation': conversation, 'conv_messages': conv_messages,
    })


def _ai_reply(user_message):
    """Simple rule-based canned-response assistant for common gym operations questions."""
    msg = user_message.lower()
    rules = [
        (['revenue', 'income', 'earning'], "You can find detailed revenue breakdowns under Reports → Revenue Reports, or check the Revenue Forecast page for projections."),
        (['churn', 'risk', 'cancel'], "Check the Member Churn Prediction page — it flags members with declining attendance or expiring memberships as at-risk."),
        (['workout', 'exercise', 'plan'], "I can generate a personalized workout plan! Head to the AI Workout Generator and select a member, goal, and fitness level."),
        (['nutrition', 'diet', 'calorie'], "Use the AI Nutrition Advisor to calculate BMR, TDEE, and macro targets for any member."),
        (['attendance', 'visit', 'checkin'], "The Attendance Prediction page forecasts expected visits based on historical patterns."),
        (['member', 'new member', 'sign up'], "You can add new members from the Members section, or check Smart Recommendations for engagement ideas."),
        (['hello', 'hi', 'hey'], "Hello! I'm your GymX AI assistant. Ask me about revenue, churn risk, workouts, nutrition, or attendance trends."),
    ]
    for keywords, reply in rules:
        if any(k in msg for k in keywords):
            return reply
    return "I'm not sure about that yet, but I can help with revenue forecasts, churn risk, workout plans, nutrition advice, or attendance predictions. Try asking about one of those!"


@role_required(*ADMIN_ROLES)
def chat_send(request):
    if request.method == 'POST':
        conversation, _ = ChatConversation.objects.get_or_create(user=request.user, defaults={'title': 'Assistant Chat'})
        user_msg = request.POST.get('message', '').strip()
        if user_msg:
            ChatMessage.objects.create(conversation=conversation, sender='user', message=user_msg)
            reply = _ai_reply(user_msg)
            ChatMessage.objects.create(conversation=conversation, sender='ai', message=reply)
            return JsonResponse({'status': 'ok', 'reply': reply})
        return JsonResponse({'status': 'error', 'message': 'Empty message.'})
    return JsonResponse({'status': 'error'}, status=405)


# ── 5. Smart Recommendations ────────────────────────────────
@role_required(*ADMIN_ROLES)
def smart_recommendations(request):
    today = date.today()
    recommendations = []

    # Members who haven't visited in 14+ days but have active subscriptions
    inactive_members = []
    for m in Member.objects.filter(status='active'):
        last_visit = AttendanceRecord.objects.filter(member=m).order_by('-date').first()
        if last_visit and (today - last_visit.date).days >= 14:
            inactive_members.append(m)
        elif not last_visit:
            inactive_members.append(m)

    if inactive_members:
        recommendations.append({
            'title': 'Re-engagement Campaign',
            'description': f'{len(inactive_members)} active members haven\'t visited in 14+ days. Consider a personalized email or SMS campaign.',
            'icon': 'fa-envelope', 'color': 'orange', 'members': inactive_members[:8],
        })

    # Best-selling POS products to restock/promote
    top_products = Sale.objects.filter(status='completed').values('items__product_name').annotate(
        total=Sum('items__quantity')
    ).order_by('-total')[:5] if Sale.objects.exists() else []
    if top_products:
        recommendations.append({
            'title': 'Trending Products',
            'description': 'These products are selling well — consider a bundle promotion or featured display.',
            'icon': 'fa-cart-shopping', 'color': 'green', 'products': top_products,
        })

    # Expiring memberships — upsell renewal
    expiring = MemberSubscription.objects.filter(status='active', end_date__lte=today + timedelta(days=7), end_date__gte=today)
    if expiring.exists():
        recommendations.append({
            'title': 'Renewal Opportunities',
            'description': f'{expiring.count()} membership(s) expiring within 7 days. Reach out with a renewal incentive.',
            'icon': 'fa-rotate', 'color': 'blue', 'count': expiring.count(),
        })

    return render(request, 'aifeatures/recommendations.html', {'recommendations': recommendations})


# ── 6. Member Churn Prediction ──────────────────────────────
def _compute_churn_scores():
    today = date.today()
    scores = []
    for m in Member.objects.filter(status='active').select_related():
        last_visit = AttendanceRecord.objects.filter(member=m).order_by('-date').first()
        days_since_visit = (today - last_visit.date).days if last_visit else 999
        sub = MemberSubscription.objects.filter(member=m, status='active').order_by('-end_date').first()
        days_left = (sub.end_date - today).days if sub else -1
        pending_payments = Payment.objects.filter(member=m, status='pending').count()

        risk_score = 0
        risk_score += min(days_since_visit * 2, 60)
        if days_left < 0: risk_score += 20
        elif days_left <= 7: risk_score += 15
        risk_score += pending_payments * 10
        risk_score = min(risk_score, 100)

        risk_level = 'High' if risk_score >= 60 else ('Medium' if risk_score >= 30 else 'Low')
        scores.append({
            'member': m, 'risk_score': risk_score, 'risk_level': risk_level,
            'days_since_visit': days_since_visit, 'days_left': days_left,
        })
    scores.sort(key=lambda x: x['risk_score'], reverse=True)
    return scores


@role_required(*ADMIN_ROLES)
def churn_prediction(request):
    scores = _compute_churn_scores()
    stats = {
        'high': sum(1 for s in scores if s['risk_level'] == 'High'),
        'medium': sum(1 for s in scores if s['risk_level'] == 'Medium'),
        'low': sum(1 for s in scores if s['risk_level'] == 'Low'),
    }
    return render(request, 'aifeatures/churn_prediction.html', {'scores': scores[:30], 'stats': stats})


# ── 7. Revenue Forecast ──────────────────────────────────────
def _forecast_revenue():
    today = date.today()
    history = []
    for i in range(5, -1, -1):
        d = today.replace(day=1) - timedelta(days=i * 30)
        rev = Payment.objects.filter(status='completed', payment_date__year=d.year, payment_date__month=d.month).aggregate(t=Sum('net_amount'))['t'] or 0
        history.append({'label': d.strftime('%b'), 'value': float(rev)})

    values = [h['value'] for h in history if h['value'] > 0]
    avg_growth = 0
    if len(values) >= 2:
        growths = [(values[i] - values[i-1]) / values[i-1] for i in range(1, len(values)) if values[i-1] > 0]
        avg_growth = sum(growths) / len(growths) if growths else 0

    last_value = values[-1] if values else 0
    forecast = []
    projected = last_value
    for i in range(3):
        projected = projected * (1 + avg_growth)
        forecast.append(round(projected))

    return {'history': history, 'forecast': forecast, 'avg_growth_pct': round(avg_growth * 100, 1)}


@role_required(*ADMIN_ROLES)
def revenue_forecast(request):
    data = _forecast_revenue()
    return render(request, 'aifeatures/revenue_forecast.html', data)


# ── 8. Attendance Prediction ──────────────────────────────────
def _forecast_attendance():
    today = date.today()
    history = []
    for i in range(7, -1, -1):
        week_start = today - timedelta(weeks=i+1)
        week_end = today - timedelta(weeks=i)
        count = AttendanceRecord.objects.filter(date__gte=week_start, date__lt=week_end).count()
        history.append({'label': f'Wk -{i}' if i > 0 else 'This Wk', 'value': count})

    values = [h['value'] for h in history]
    avg = sum(values) / len(values) if values else 0
    recent_avg = sum(values[-3:]) / len(values[-3:]) if len(values) >= 3 else avg
    trend = recent_avg - avg

    forecast = []
    projected = recent_avg
    for i in range(3):
        projected = max(projected + trend * 0.3, 0)
        forecast.append(round(projected))

    return {'history': history, 'forecast': forecast, 'weekly_avg': round(avg)}


@role_required(*ADMIN_ROLES)
def attendance_prediction(request):
    data = _forecast_attendance()
    return render(request, 'aifeatures/attendance_prediction.html', data)
