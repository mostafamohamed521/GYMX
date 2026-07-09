from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone

from .models import (
    Food, FoodCategory, Ingredient, Meal, MealFood,
    NutritionPlan, MealPlan, WaterIntake, Supplement, NutritionLog,
)
from apps.members.models import Member
from apps.coaches.models import Coach


# ── 1. Nutrition Plans ─────────────────────────────────────
@login_required
def nutrition_plans(request):
    plans    = NutritionPlan.objects.select_related('member','coach').order_by('-created_at')
    q        = request.GET.get('q','')
    status_f = request.GET.get('status','')
    goal_f   = request.GET.get('goal','')

    if q:        plans = plans.filter(Q(member__first_name__icontains=q)|Q(member__last_name__icontains=q)|Q(name__icontains=q))
    if status_f: plans = plans.filter(status=status_f)
    if goal_f:   plans = plans.filter(goal=goal_f)

    stats = {
        'total':   NutritionPlan.objects.count(),
        'active':  NutritionPlan.objects.filter(status='active').count(),
        'members': NutritionPlan.objects.values('member').distinct().count(),
        'meals':   Meal.objects.filter(is_active=True).count(),
    }
    return render(request, 'nutrition/nutrition_plans.html', {
        'plans': plans[:100], 'stats': stats,
        'q': q, 'status_f': status_f, 'goal_f': goal_f,
        'statuses': NutritionPlan.Status.choices,
        'goals': NutritionPlan.Goal.choices,
    })


# ── 2. New Plan ────────────────────────────────────────────
@login_required
def plan_new(request):
    if request.method == 'POST':
        try:
            member   = get_object_or_404(Member, pk=request.POST.get('member'))
            coach_pk = request.POST.get('coach')
            plan = NutritionPlan.objects.create(
                member         = member,
                coach          = Coach.objects.filter(pk=coach_pk).first() if coach_pk else None,
                name           = request.POST.get('name'),
                goal           = request.POST.get('goal','health'),
                daily_calories = int(request.POST.get('daily_calories',2000)),
                daily_protein  = float(request.POST.get('daily_protein',150)),
                daily_carbs    = float(request.POST.get('daily_carbs',250)),
                daily_fat      = float(request.POST.get('daily_fat',65)),
                daily_water_ml = int(request.POST.get('daily_water_ml',2500)),
                start_date     = request.POST.get('start_date') or date.today(),
                end_date       = request.POST.get('end_date') or None,
                notes          = request.POST.get('notes',''),
                created_by     = request.user,
            )
            messages.success(request, f'Nutrition plan "{plan.name}" created!')
            return redirect('nutrition:plan_detail', pk=plan.pk)
        except Exception as e:
            messages.error(request, f'Error: {e}')

    members = Member.objects.filter(status='active').order_by('first_name')
    coaches = Coach.objects.filter(status='active')
    return render(request, 'nutrition/plan_form.html', {
        'members': members, 'coaches': coaches,
        'goals': NutritionPlan.Goal.choices, 'today': date.today(),
    })


# ── 3. Plan Detail ─────────────────────────────────────────
@login_required
def plan_detail(request, pk):
    plan     = get_object_or_404(NutritionPlan.objects.select_related('member','coach'), pk=pk)
    meal_plan_entries = MealPlan.objects.filter(nutrition_plan=plan).select_related('meal').order_by('day_of_week','meal_order')
    days     = {i: [] for i in range(7)}
    for entry in meal_plan_entries:
        days[entry.day_of_week].append(entry)
    day_names = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']

    today = date.today()
    log_today = NutritionLog.objects.filter(member=plan.member, date=today).first()

    if request.method == 'POST' and request.POST.get('action') == 'log':
        log, _ = NutritionLog.objects.update_or_create(
            member=plan.member, date=today,
            defaults={
                'calories_target': plan.daily_calories,
                'calories_actual': int(request.POST.get('calories',0)),
                'protein_actual':  float(request.POST.get('protein',0)),
                'carbs_actual':    float(request.POST.get('carbs',0)),
                'fat_actual':      float(request.POST.get('fat',0)),
                'water_ml':        int(request.POST.get('water',0)),
                'notes':           request.POST.get('notes',''),
            }
        )
        messages.success(request, f'Nutrition log saved for {today}.')
        return redirect('nutrition:plan_detail', pk=pk)

    return render(request, 'nutrition/plan_detail.html', {
        'plan': plan, 'days': days, 'day_names': day_names,
        'log_today': log_today, 'today': today,
    })


# ── 4. Meal Plans ──────────────────────────────────────────
@login_required
def meal_plans(request):
    plans = NutritionPlan.objects.select_related('member').filter(status='active')
    return render(request, 'nutrition/meal_plans.html', {'plans': plans})


@login_required
def meal_plan_add(request, plan_pk):
    plan = get_object_or_404(NutritionPlan, pk=plan_pk)
    if request.method == 'POST':
        meal = get_object_or_404(Meal, pk=request.POST.get('meal'))
        MealPlan.objects.create(
            nutrition_plan=plan,
            day_of_week=int(request.POST.get('day_of_week',0)),
            meal=meal,
            meal_order=int(request.POST.get('meal_order',1)),
            notes=request.POST.get('notes',''),
        )
        messages.success(request, f'{meal.name} added to plan.')
        return redirect('nutrition:plan_detail', pk=plan_pk)

    meals = Meal.objects.filter(is_active=True)
    return render(request, 'nutrition/meal_plan_add.html', {
        'plan': plan, 'meals': meals,
        'days': MealPlan.DayOfWeek.choices,
    })


# ── 5. Meals Library ───────────────────────────────────────
@login_required
def meals_library(request):
    meals  = Meal.objects.filter(is_active=True)
    q      = request.GET.get('q','')
    type_f = request.GET.get('type','')
    if q:      meals = meals.filter(Q(name__icontains=q)|Q(description__icontains=q))
    if type_f: meals = meals.filter(meal_type=type_f)

    stats = {
        'total':     Meal.objects.filter(is_active=True).count(),
        'breakfast': Meal.objects.filter(meal_type='breakfast').count(),
        'lunch':     Meal.objects.filter(meal_type='lunch').count(),
        'dinner':    Meal.objects.filter(meal_type='dinner').count(),
    }
    return render(request, 'nutrition/meals_library.html', {
        'meals': meals, 'stats': stats,
        'q': q, 'type_f': type_f,
        'meal_types': Meal.MealType.choices,
    })


@login_required
def meal_new(request):
    if request.method == 'POST':
        try:
            meal = Meal.objects.create(
                name          = request.POST.get('name'),
                meal_type     = request.POST.get('meal_type','breakfast'),
                description   = request.POST.get('description',''),
                instructions  = request.POST.get('instructions',''),
                prep_time_min = int(request.POST.get('prep_time_min',10)),
                total_calories= float(request.POST.get('total_calories',0)),
                total_protein = float(request.POST.get('total_protein',0)),
                total_carbs   = float(request.POST.get('total_carbs',0)),
                total_fat     = float(request.POST.get('total_fat',0)),
                created_by    = request.user,
            )
            messages.success(request, f'Meal "{meal.name}" added!')
            return redirect('nutrition:meals')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    foods = Food.objects.filter(is_active=True)
    return render(request, 'nutrition/meal_form.html', {
        'meal_types': Meal.MealType.choices, 'foods': foods,
    })


# ── 6. Food Database ───────────────────────────────────────
@login_required
def food_database(request):
    foods  = Food.objects.select_related('category').filter(is_active=True)
    q      = request.GET.get('q','')
    cat_f  = request.GET.get('category','')
    if q:     foods = foods.filter(Q(name__icontains=q))
    if cat_f: foods = foods.filter(category__pk=cat_f)

    cats  = FoodCategory.objects.all()
    stats = {
        'total':    Food.objects.filter(is_active=True).count(),
        'categories': FoodCategory.objects.count(),
        'avg_cal':  Food.objects.filter(is_active=True).aggregate(a=Avg('calories'))['a'] or 0,
    }
    return render(request, 'nutrition/food_database.html', {
        'foods': foods[:200], 'cats': cats, 'stats': stats,
        'q': q, 'cat_f': cat_f,
    })


@login_required
def food_new(request):
    if request.method == 'POST':
        try:
            cat_pk = request.POST.get('category')
            Food.objects.create(
                name         = request.POST.get('name'),
                category     = FoodCategory.objects.filter(pk=cat_pk).first() if cat_pk else None,
                serving_size = float(request.POST.get('serving_size',100)),
                serving_unit = request.POST.get('serving_unit','g'),
                calories     = float(request.POST.get('calories',0)),
                protein      = float(request.POST.get('protein',0)),
                carbs        = float(request.POST.get('carbs',0)),
                fat          = float(request.POST.get('fat',0)),
                fiber        = float(request.POST.get('fiber',0)),
                sugar        = float(request.POST.get('sugar',0)),
                sodium       = float(request.POST.get('sodium',0)),
                created_by   = request.user,
            )
            messages.success(request, 'Food added!')
            return redirect('nutrition:foods')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    cats = FoodCategory.objects.all()
    return render(request, 'nutrition/food_form.html', {
        'cats': cats, 'units': Food.Unit.choices,
    })


# ── 7. Ingredients ─────────────────────────────────────────
@login_required
def ingredients(request):
    if request.method == 'POST':
        Ingredient.objects.get_or_create(
            name=request.POST.get('name'),
            defaults={'description': request.POST.get('description','')}
        )
        messages.success(request, 'Ingredient added.')
        return redirect('nutrition:ingredients')
    items = Ingredient.objects.all()
    return render(request, 'nutrition/ingredients.html', {'items': items})


# ── 8. Calories Calculator ─────────────────────────────────
@login_required
def calories_calculator(request):
    result = None
    if request.method == 'POST':
        try:
            weight = float(request.POST.get('weight',0))
            height = float(request.POST.get('height',0))
            age    = int(request.POST.get('age',0))
            gender = request.POST.get('gender','male')
            activity = request.POST.get('activity','sedentary')
            goal   = request.POST.get('goal','maintain')

            # Mifflin-St Jeor
            if gender == 'male':
                bmr = 10*weight + 6.25*height - 5*age + 5
            else:
                bmr = 10*weight + 6.25*height - 5*age - 161

            multipliers = {'sedentary':1.2,'light':1.375,'moderate':1.55,'active':1.725,'very_active':1.9}
            tdee = bmr * multipliers.get(activity, 1.2)

            if goal == 'lose': calories = tdee - 500
            elif goal == 'gain': calories = tdee + 500
            else: calories = tdee

            result = {
                'bmr': round(bmr),
                'tdee': round(tdee),
                'target': round(calories),
                'protein': round(calories * 0.3 / 4),
                'carbs': round(calories * 0.4 / 4),
                'fat': round(calories * 0.3 / 9),
                'weight': weight, 'height': height, 'age': age,
                'gender': gender, 'activity': activity, 'goal': goal,
            }
        except Exception as e:
            messages.error(request, f'Error: {e}')

    members = Member.objects.filter(status='active').order_by('first_name')
    return render(request, 'nutrition/calories_calculator.html', {
        'result': result, 'members': members,
    })


# ── 9. BMI Calculator ──────────────────────────────────────
@login_required
def bmi_calculator(request):
    result = None
    if request.method == 'POST':
        try:
            weight = float(request.POST.get('weight',0))
            height = float(request.POST.get('height',0)) / 100
            bmi    = weight / (height ** 2)

            if bmi < 18.5:   category, color = 'Underweight', '#3B82F6'
            elif bmi < 25:   category, color = 'Normal Weight', '#10B981'
            elif bmi < 30:   category, color = 'Overweight', '#F59E0B'
            else:            category, color = 'Obese', '#EF4444'

            ideal_min = 18.5 * (height ** 2)
            ideal_max = 24.9 * (height ** 2)

            result = {
                'bmi': round(bmi, 1),
                'category': category,
                'color': color,
                'ideal_min': round(ideal_min, 1),
                'ideal_max': round(ideal_max, 1),
                'weight': weight,
                'height': weight,
            }
        except Exception as e:
            messages.error(request, f'Error: {e}')

    return render(request, 'nutrition/bmi_calculator.html', {'result': result})


# ── 10. BMR Calculator ─────────────────────────────────────
@login_required
def bmr_calculator(request):
    result = None
    if request.method == 'POST':
        try:
            weight = float(request.POST.get('weight',0))
            height = float(request.POST.get('height',0))
            age    = int(request.POST.get('age',25))
            gender = request.POST.get('gender','male')

            if gender == 'male':
                bmr_ms = 10*weight + 6.25*height - 5*age + 5
                bmr_h  = 66.47 + 13.75*weight + 5.003*height - 6.755*age
            else:
                bmr_ms = 10*weight + 6.25*height - 5*age - 161
                bmr_h  = 655.1 + 9.563*weight + 1.85*height - 4.676*age

            result = {
                'mifflin': round(bmr_ms),
                'harris':  round(bmr_h),
                'avg':     round((bmr_ms + bmr_h) / 2),
                'sedentary':   round(bmr_ms * 1.2),
                'light':       round(bmr_ms * 1.375),
                'moderate':    round(bmr_ms * 1.55),
                'active':      round(bmr_ms * 1.725),
                'very_active': round(bmr_ms * 1.9),
                'weight': weight, 'height': height, 'age': age, 'gender': gender,
            }
        except Exception as e:
            messages.error(request, f'Error: {e}')

    return render(request, 'nutrition/bmr_calculator.html', {'result': result})


# ── 11. Water Intake ───────────────────────────────────────
@login_required
def water_intake(request):
    today   = date.today()
    member_pk = request.GET.get('member')
    member  = Member.objects.filter(pk=member_pk).first() if member_pk else None
    members = Member.objects.filter(status='active').order_by('first_name')

    logs = WaterIntake.objects.filter(date=today)
    if member: logs = logs.filter(member=member)

    stats = {
        'total_today': logs.aggregate(t=Sum('amount_ml'))['t'] or 0,
        'entries': logs.count(),
    }
    weekly = []
    for i in range(6,-1,-1):
        d = today - timedelta(days=i)
        amt = WaterIntake.objects.filter(date=d).aggregate(t=Sum('amount_ml'))['t'] or 0
        weekly.append({'label': d.strftime('%a'), 'amount': amt})

    return render(request, 'nutrition/water_intake.html', {
        'logs': logs.select_related('member')[:50], 'stats': stats,
        'members': members, 'member': member,
        'today': today, 'weekly': weekly,
    })


@login_required
def water_log(request):
    if request.method == 'POST':
        member = get_object_or_404(Member, pk=request.POST.get('member'))
        WaterIntake.objects.create(
            member=member,
            amount_ml=int(request.POST.get('amount_ml',250)),
            date=request.POST.get('date') or date.today(),
            notes=request.POST.get('notes',''),
        )
        messages.success(request, f'{request.POST.get("amount_ml")}ml logged for {member.get_full_name()}!')
    return redirect('nutrition:water')


# ── 12. Supplements ────────────────────────────────────────
@login_required
def supplements(request):
    sups = Supplement.objects.select_related('member').order_by('-is_active','name')
    member_pk = request.GET.get('member')
    if member_pk: sups = sups.filter(member__pk=member_pk)
    members = Member.objects.filter(status='active').order_by('first_name')
    stats = {
        'total':  sups.count(),
        'active': sups.filter(is_active=True).count(),
    }
    return render(request, 'nutrition/supplements.html', {
        'sups': sups, 'stats': stats, 'members': members,
        'member_pk': member_pk,
    })


@login_required
def supplement_new(request):
    if request.method == 'POST':
        try:
            member = get_object_or_404(Member, pk=request.POST.get('member'))
            Supplement.objects.create(
                member    = member,
                name      = request.POST.get('name'),
                brand     = request.POST.get('brand',''),
                dosage    = request.POST.get('dosage'),
                frequency = request.POST.get('frequency','daily'),
                start_date= request.POST.get('start_date') or date.today(),
                end_date  = request.POST.get('end_date') or None,
                notes     = request.POST.get('notes',''),
            )
            messages.success(request, 'Supplement added!')
            return redirect('nutrition:supplements')
        except Exception as e:
            messages.error(request, f'Error: {e}')

    members = Member.objects.filter(status='active').order_by('first_name')
    return render(request, 'nutrition/supplement_form.html', {
        'members': members, 'frequencies': Supplement.Frequency.choices,
        'today': date.today(),
    })


# ── 13. Assign Diet ────────────────────────────────────────
@login_required
def assign_diet(request):
    if request.method == 'POST':
        member   = get_object_or_404(Member, pk=request.POST.get('member'))
        coach_pk = request.POST.get('coach')
        plan = NutritionPlan.objects.create(
            member         = member,
            coach          = Coach.objects.filter(pk=coach_pk).first() if coach_pk else None,
            name           = request.POST.get('name', f'{member.get_full_name()} Diet Plan'),
            goal           = request.POST.get('goal','health'),
            daily_calories = int(request.POST.get('daily_calories',2000)),
            daily_protein  = float(request.POST.get('daily_protein',150)),
            daily_carbs    = float(request.POST.get('daily_carbs',250)),
            daily_fat      = float(request.POST.get('daily_fat',65)),
            daily_water_ml = 2500,
            start_date     = request.POST.get('start_date') or date.today(),
            created_by     = request.user,
        )
        messages.success(request, f'Diet plan assigned to {member.get_full_name()}!')
        return redirect('nutrition:plan_detail', pk=plan.pk)

    members = Member.objects.filter(status='active').order_by('first_name')
    coaches = Coach.objects.filter(status='active')
    return render(request, 'nutrition/assign_diet.html', {
        'members': members, 'coaches': coaches,
        'goals': NutritionPlan.Goal.choices, 'today': date.today(),
    })


# ── 14. Nutrition Progress ─────────────────────────────────
@login_required
def nutrition_progress(request, member_pk):
    member = get_object_or_404(Member, pk=member_pk)
    plans  = NutritionPlan.objects.filter(member=member)
    active = plans.filter(status='active').first()
    logs   = NutritionLog.objects.filter(member=member).order_by('-date')[:30]

    stats = {
        'total_plans': plans.count(),
        'avg_calories': logs.aggregate(a=Avg('calories_actual'))['a'] or 0,
        'avg_water':    logs.aggregate(a=Avg('water_ml'))['a'] or 0,
        'logs_count':   logs.count(),
    }
    monthly = []
    today = date.today()
    for i in range(5,-1,-1):
        d = today.replace(day=1) - timedelta(days=i*30)
        avg = NutritionLog.objects.filter(
            member=member, date__year=d.year, date__month=d.month
        ).aggregate(a=Avg('calories_actual'))['a'] or 0
        monthly.append({'label': d.strftime('%b'), 'avg': round(avg)})

    return render(request, 'nutrition/nutrition_progress.html', {
        'member': member, 'plans': plans, 'active': active,
        'logs': logs, 'stats': stats, 'monthly': monthly,
    })


# ── 15. Nutrition History ──────────────────────────────────
@login_required
def nutrition_history(request, member_pk):
    member = get_object_or_404(Member, pk=member_pk)
    logs   = NutritionLog.objects.filter(member=member).order_by('-date')
    return render(request, 'nutrition/nutrition_history.html', {
        'member': member, 'logs': logs, 'total': logs.count(),
    })
