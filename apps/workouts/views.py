from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone

from .models import (
    Exercise, ExerciseCategory, WorkoutTemplate, WorkoutPlan,
    WorkoutSession, SessionExercise, PTSession,
)
from apps.members.models import Member
from apps.coaches.models import Coach


# ── 1. Workout Plans ───────────────────────────────────────
@login_required
def workout_plans(request):
    plans = WorkoutPlan.objects.select_related('member','coach').order_by('-created_at')
    q        = request.GET.get('q','')
    status_f = request.GET.get('status','')
    goal_f   = request.GET.get('goal','')

    if q:
        plans = plans.filter(Q(member__first_name__icontains=q)|Q(member__last_name__icontains=q)|Q(name__icontains=q))
    if status_f: plans = plans.filter(status=status_f)
    if goal_f:   plans = plans.filter(goal=goal_f)

    stats = {
        'total':     WorkoutPlan.objects.count(),
        'active':    WorkoutPlan.objects.filter(status='active').count(),
        'completed': WorkoutPlan.objects.filter(status='completed').count(),
        'sessions_today': WorkoutSession.objects.filter(scheduled_date=date.today()).count(),
    }

    return render(request, 'workouts/workout_plans.html', {
        'plans': plans[:100], 'stats': stats,
        'q': q, 'status_f': status_f, 'goal_f': goal_f,
        'statuses': WorkoutPlan.Status.choices,
        'goals': WorkoutTemplate.Goal.choices,
    })


# ── 2. New Plan ────────────────────────────────────────────
@login_required
def plan_new(request):
    if request.method == 'POST':
        try:
            member = get_object_or_404(Member, pk=request.POST.get('member'))
            coach_pk = request.POST.get('coach')
            plan = WorkoutPlan.objects.create(
                member     = member,
                coach      = Coach.objects.filter(pk=coach_pk).first() if coach_pk else None,
                name       = request.POST.get('name'),
                goal       = request.POST.get('goal','general'),
                start_date = request.POST.get('start_date') or date.today(),
                end_date   = request.POST.get('end_date') or None,
                notes      = request.POST.get('notes',''),
                created_by = request.user,
            )
            messages.success(request, f'Workout plan "{plan.name}" created!')
            return redirect('workouts:plan_detail', pk=plan.pk)
        except Exception as e:
            messages.error(request, f'Error: {e}')

    members   = Member.objects.filter(status='active').order_by('first_name')
    coaches   = Coach.objects.filter(status='active')
    templates = WorkoutTemplate.objects.all()
    return render(request, 'workouts/plan_form.html', {
        'members': members, 'coaches': coaches, 'templates': templates,
        'goals': WorkoutTemplate.Goal.choices, 'today': date.today(),
    })


# ── 3. Plan Detail ─────────────────────────────────────────
@login_required
def plan_detail(request, pk):
    plan = get_object_or_404(WorkoutPlan.objects.select_related('member','coach').prefetch_related('sessions'), pk=pk)
    today = date.today()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_session':
            WorkoutSession.objects.create(
                plan           = plan,
                name           = request.POST.get('session_name', 'Workout Session'),
                scheduled_date = request.POST.get('scheduled_date'),
                notes          = request.POST.get('notes',''),
            )
            messages.success(request, 'Session added.')
        elif action == 'complete':
            session = get_object_or_404(WorkoutSession, pk=request.POST.get('session_pk'), plan=plan)
            session.status       = 'completed'
            session.completed_date = today
            session.duration_min = request.POST.get('duration_min') or None
            session.calories_burned = request.POST.get('calories') or None
            session.save()
            messages.success(request, 'Session marked complete!')
        return redirect('workouts:plan_detail', pk=pk)

    upcoming = plan.sessions.filter(scheduled_date__gte=today, status='scheduled').order_by('scheduled_date')
    past     = plan.sessions.filter(Q(status='completed')|Q(scheduled_date__lt=today)).order_by('-scheduled_date')[:10]

    return render(request, 'workouts/plan_detail.html', {
        'plan': plan, 'upcoming': upcoming, 'past': past, 'today': today,
    })


# ── 4. Workout Templates ───────────────────────────────────
@login_required
def workout_templates(request):
    templates = WorkoutTemplate.objects.all().order_by('name')
    goal_f = request.GET.get('goal','')
    diff_f = request.GET.get('difficulty','')
    if goal_f: templates = templates.filter(goal=goal_f)
    if diff_f: templates = templates.filter(difficulty=diff_f)

    return render(request, 'workouts/workout_templates.html', {
        'templates': templates, 'goal_f': goal_f, 'diff_f': diff_f,
        'goals': WorkoutTemplate.Goal.choices,
        'difficulties': Exercise.Difficulty.choices,
    })


# ── 5. New Template ────────────────────────────────────────
@login_required
def template_new(request):
    if request.method == 'POST':
        tmpl = WorkoutTemplate.objects.create(
            name            = request.POST.get('name'),
            description     = request.POST.get('description',''),
            goal            = request.POST.get('goal','general'),
            difficulty      = request.POST.get('difficulty','beginner'),
            duration_weeks  = int(request.POST.get('duration_weeks',4)),
            days_per_week   = int(request.POST.get('days_per_week',3)),
            session_duration= int(request.POST.get('session_duration',60)),
            is_public       = bool(request.POST.get('is_public')),
            created_by      = request.user,
        )
        messages.success(request, f'Template "{tmpl.name}" created!')
        return redirect('workouts:templates')

    return render(request, 'workouts/template_form.html', {
        'goals': WorkoutTemplate.Goal.choices,
        'difficulties': Exercise.Difficulty.choices,
    })


# ── 6. Exercise Library ────────────────────────────────────
@login_required
def exercise_library(request):
    exercises = Exercise.objects.select_related('category').filter(is_active=True)
    q        = request.GET.get('q','')
    muscle_f = request.GET.get('muscle','')
    diff_f   = request.GET.get('difficulty','')
    equip_f  = request.GET.get('equipment','')
    cat_f    = request.GET.get('category','')

    if q:       exercises = exercises.filter(Q(name__icontains=q)|Q(description__icontains=q))
    if muscle_f: exercises = exercises.filter(muscle_group=muscle_f)
    if diff_f:   exercises = exercises.filter(difficulty=diff_f)
    if equip_f:  exercises = exercises.filter(equipment=equip_f)
    if cat_f:    exercises = exercises.filter(category__pk=cat_f)

    categories = ExerciseCategory.objects.all()
    stats = {
        'total':      Exercise.objects.filter(is_active=True).count(),
        'categories': ExerciseCategory.objects.count(),
        'beginner':   Exercise.objects.filter(difficulty='beginner').count(),
        'advanced':   Exercise.objects.filter(difficulty='advanced').count(),
    }

    return render(request, 'workouts/exercise_library.html', {
        'exercises': exercises[:200], 'stats': stats,
        'categories': categories,
        'q': q, 'muscle_f': muscle_f, 'diff_f': diff_f, 'equip_f': equip_f, 'cat_f': cat_f,
        'muscles': Exercise.MuscleGroup.choices,
        'difficulties': Exercise.Difficulty.choices,
        'equipments': Exercise.Equipment.choices,
    })


# ── 7. Exercise Categories ─────────────────────────────────
@login_required
def exercise_categories(request):
    if request.method == 'POST':
        ExerciseCategory.objects.create(
            name        = request.POST.get('name'),
            description = request.POST.get('description',''),
            icon        = request.POST.get('icon','fa-dumbbell'),
            color       = request.POST.get('color','#3B82F6'),
        )
        messages.success(request, 'Category added.')
        return redirect('workouts:categories')

    cats = ExerciseCategory.objects.annotate(ex_count=Count('exercises')).order_by('name')
    return render(request, 'workouts/exercise_categories.html', {'cats': cats})


# ── 8. Exercise Detail ─────────────────────────────────────
@login_required
def exercise_detail(request, pk):
    exercise = get_object_or_404(Exercise, pk=pk)
    related  = Exercise.objects.filter(muscle_group=exercise.muscle_group, is_active=True).exclude(pk=pk)[:4]
    return render(request, 'workouts/exercise_detail.html', {
        'exercise': exercise, 'related': related,
    })


# ── 9. New Exercise ────────────────────────────────────────
@login_required
def exercise_new(request):
    if request.method == 'POST':
        try:
            ex = Exercise(
                name           = request.POST.get('name'),
                muscle_group   = request.POST.get('muscle_group','chest'),
                secondary_muscles = request.POST.get('secondary_muscles',''),
                equipment      = request.POST.get('equipment','dumbbell'),
                difficulty     = request.POST.get('difficulty','beginner'),
                description    = request.POST.get('description',''),
                instructions   = request.POST.get('instructions',''),
                tips           = request.POST.get('tips',''),
                video_url      = request.POST.get('video_url',''),
                calories_per_min = float(request.POST.get('calories_per_min',5)),
                created_by     = request.user,
            )
            cat_pk = request.POST.get('category')
            if cat_pk:
                ex.category = ExerciseCategory.objects.filter(pk=cat_pk).first()
            if 'image' in request.FILES:
                ex.image = request.FILES['image']
            ex.save()
            messages.success(request, f'Exercise "{ex.name}" added!')
            return redirect('workouts:exercise_detail', pk=ex.pk)
        except Exception as e:
            messages.error(request, f'Error: {e}')

    return render(request, 'workouts/exercise_form.html', {
        'categories': ExerciseCategory.objects.all(),
        'muscles': Exercise.MuscleGroup.choices,
        'difficulties': Exercise.Difficulty.choices,
        'equipments': Exercise.Equipment.choices,
    })


# ── 10. Workout Builder ────────────────────────────────────
@login_required
def workout_builder(request):
    exercises   = Exercise.objects.filter(is_active=True).select_related('category').order_by('name')
    members     = Member.objects.filter(status='active').order_by('first_name')
    coaches     = Coach.objects.filter(status='active')
    categories  = ExerciseCategory.objects.all()
    muscles     = Exercise.MuscleGroup.choices
    goals       = WorkoutTemplate.Goal.choices

    if request.method == 'POST':
        try:
            member = get_object_or_404(Member, pk=request.POST.get('member'))
            coach_pk = request.POST.get('coach')
            plan = WorkoutPlan.objects.create(
                member     = member,
                coach      = Coach.objects.filter(pk=coach_pk).first() if coach_pk else None,
                name       = request.POST.get('plan_name','Custom Workout'),
                goal       = request.POST.get('goal','general'),
                start_date = request.POST.get('start_date') or date.today(),
                created_by = request.user,
            )
            # Create one session with selected exercises
            session = WorkoutSession.objects.create(
                plan=plan, name='Session 1',
                scheduled_date=request.POST.get('start_date') or date.today(),
            )
            ex_ids = request.POST.getlist('exercise_ids')
            for i, ex_id in enumerate(ex_ids, 1):
                ex = Exercise.objects.filter(pk=ex_id).first()
                if ex:
                    SessionExercise.objects.create(
                        session=session, exercise=ex, order=i,
                        sets=int(request.POST.get(f'sets_{ex_id}',3)),
                        reps=request.POST.get(f'reps_{ex_id}','10'),
                        rest_sec=int(request.POST.get(f'rest_{ex_id}',60)),
                    )
            messages.success(request, f'Workout "{plan.name}" built and assigned to {member.get_full_name()}!')
            return redirect('workouts:plan_detail', pk=plan.pk)
        except Exception as e:
            messages.error(request, f'Error: {e}')

    return render(request, 'workouts/workout_builder.html', {
        'exercises': exercises, 'members': members, 'coaches': coaches,
        'categories': categories, 'muscles': muscles, 'goals': goals,
        'today': date.today(),
    })


# ── 11. Assign Workout ─────────────────────────────────────
@login_required
def assign_workout(request):
    if request.method == 'POST':
        member   = get_object_or_404(Member, pk=request.POST.get('member'))
        template = get_object_or_404(WorkoutTemplate, pk=request.POST.get('template'))
        coach_pk = request.POST.get('coach')
        start    = request.POST.get('start_date') or date.today()
        plan = WorkoutPlan.objects.create(
            member=member, template=template,
            coach=Coach.objects.filter(pk=coach_pk).first() if coach_pk else None,
            name=template.name, goal=template.goal,
            start_date=start, created_by=request.user,
        )
        messages.success(request, f'"{template.name}" assigned to {member.get_full_name()}!')
        return redirect('workouts:plan_detail', pk=plan.pk)

    members   = Member.objects.filter(status='active').order_by('first_name')
    coaches   = Coach.objects.filter(status='active')
    templates = WorkoutTemplate.objects.all()
    return render(request, 'workouts/assign_workout.html', {
        'members': members, 'coaches': coaches, 'templates': templates,
        'today': date.today(),
    })


# ── 12. Workout Progress ───────────────────────────────────
@login_required
def workout_progress(request, member_pk):
    member  = get_object_or_404(Member, pk=member_pk)
    plans   = WorkoutPlan.objects.filter(member=member).prefetch_related('sessions')
    active  = plans.filter(status='active').first()
    stats = {
        'total_sessions':    WorkoutSession.objects.filter(plan__member=member, status='completed').count(),
        'total_plans':       plans.count(),
        'calories_burned':   WorkoutSession.objects.filter(plan__member=member, status='completed').aggregate(t=Sum('calories_burned'))['t'] or 0,
        'this_week':         WorkoutSession.objects.filter(plan__member=member, status='completed', completed_date__gte=date.today()-timedelta(days=7)).count(),
    }
    monthly = []
    for i in range(5,-1,-1):
        d = date.today().replace(day=1) - timedelta(days=i*30)
        c = WorkoutSession.objects.filter(plan__member=member, status='completed', completed_date__year=d.year, completed_date__month=d.month).count()
        monthly.append({'label': d.strftime('%b'), 'count': c})

    return render(request, 'workouts/workout_progress.html', {
        'member': member, 'plans': plans, 'active': active,
        'stats': stats, 'monthly': monthly,
    })


# ── 13. Workout History ────────────────────────────────────
@login_required
def workout_history(request, member_pk):
    member   = get_object_or_404(Member, pk=member_pk)
    sessions = WorkoutSession.objects.filter(plan__member=member).select_related('plan').order_by('-scheduled_date')
    return render(request, 'workouts/workout_history.html', {
        'member': member, 'sessions': sessions, 'total': sessions.count(),
    })


# ── 14. PT Sessions ────────────────────────────────────────
@login_required
def pt_sessions(request):
    sessions = PTSession.objects.select_related('member','coach').order_by('-date','-start_time')
    today    = date.today()
    status_f = request.GET.get('status','')
    if status_f: sessions = sessions.filter(status=status_f)

    stats = {
        'total':     sessions.count(),
        'today':     sessions.filter(date=today).count(),
        'scheduled': sessions.filter(status='scheduled').count(),
        'completed': sessions.filter(status='completed').count(),
    }
    return render(request, 'workouts/pt_sessions.html', {
        'sessions': sessions[:100], 'stats': stats,
        'status_f': status_f, 'statuses': PTSession.Status.choices, 'today': today,
    })


@login_required
def pt_session_new(request):
    if request.method == 'POST':
        try:
            member = get_object_or_404(Member, pk=request.POST.get('member'))
            coach  = get_object_or_404(Coach, pk=request.POST.get('coach'))
            PTSession.objects.create(
                member=member, coach=coach,
                date=request.POST.get('date'),
                start_time=request.POST.get('start_time'),
                end_time=request.POST.get('end_time'),
                notes=request.POST.get('notes',''),
                status='scheduled',
            )
            messages.success(request, 'PT Session scheduled!')
            return redirect('workouts:pt_sessions')
        except Exception as e:
            messages.error(request, f'Error: {e}')

    members = Member.objects.filter(status='active').order_by('first_name')
    coaches = Coach.objects.filter(status='active')
    return render(request, 'workouts/pt_session_form.html', {
        'members': members, 'coaches': coaches, 'today': date.today(),
    })


# ── 15. Workout Statistics ─────────────────────────────────
@login_required
def workout_statistics(request):
    today     = date.today()
    month_ago = today - timedelta(days=30)

    stats = {
        'total_plans':    WorkoutPlan.objects.count(),
        'active_plans':   WorkoutPlan.objects.filter(status='active').count(),
        'total_sessions': WorkoutSession.objects.count(),
        'completed':      WorkoutSession.objects.filter(status='completed').count(),
        'total_exercises':Exercise.objects.filter(is_active=True).count(),
        'pt_this_month':  PTSession.objects.filter(date__gte=month_ago).count(),
        'avg_duration':   WorkoutSession.objects.filter(status='completed', duration_min__isnull=False).aggregate(a=Avg('duration_min'))['a'] or 0,
        'calories_total': WorkoutSession.objects.filter(status='completed').aggregate(t=Sum('calories_burned'))['t'] or 0,
    }

    monthly = []
    for i in range(5,-1,-1):
        d = today.replace(day=1) - timedelta(days=i*30)
        c = WorkoutSession.objects.filter(status='completed', completed_date__year=d.year, completed_date__month=d.month).count()
        monthly.append({'label': d.strftime('%b'), 'count': c})

    top_members = (WorkoutSession.objects
                   .filter(status='completed')
                   .values('plan__member__first_name','plan__member__last_name','plan__member__pk')
                   .annotate(sessions=Count('id'))
                   .order_by('-sessions')[:8])

    muscle_dist = (Exercise.objects
                   .values('muscle_group')
                   .annotate(count=Count('id'))
                   .order_by('-count'))

    return render(request, 'workouts/workout_statistics.html', {
        'stats': stats, 'monthly': monthly,
        'top_members': top_members, 'muscle_dist': muscle_dist,
        'today': today,
    })


# ── AJAX ───────────────────────────────────────────────────
@login_required
def ajax_complete_session(request, pk):
    if request.method == 'POST':
        session = get_object_or_404(WorkoutSession, pk=pk)
        session.status         = 'completed'
        session.completed_date = date.today()
        session.save()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)
