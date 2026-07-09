from django.urls import path
from . import views

app_name = 'nutrition'

urlpatterns = [
    # Plans
    path('',                              views.nutrition_plans,      name='plans'),
    path('plans/new/',                    views.plan_new,             name='plan_new'),
    path('plans/<int:pk>/',              views.plan_detail,          name='plan_detail'),

    # Meal Plans
    path('meal-plans/',                   views.meal_plans,           name='meal_plans'),
    path('meal-plans/<int:plan_pk>/add/', views.meal_plan_add,        name='meal_plan_add'),

    # Meals Library
    path('meals/',                        views.meals_library,        name='meals'),
    path('meals/new/',                    views.meal_new,             name='meal_new'),

    # Food Database
    path('foods/',                        views.food_database,        name='foods'),
    path('foods/new/',                    views.food_new,             name='food_new'),

    # Ingredients
    path('ingredients/',                  views.ingredients,          name='ingredients'),

    # Calculators
    path('calculators/calories/',         views.calories_calculator,  name='calories_calc'),
    path('calculators/bmi/',              views.bmi_calculator,       name='bmi_calc'),
    path('calculators/bmr/',              views.bmr_calculator,       name='bmr_calc'),

    # Water Intake
    path('water/',                        views.water_intake,         name='water'),
    path('water/log/',                    views.water_log,            name='water_log'),

    # Supplements
    path('supplements/',                  views.supplements,          name='supplements'),
    path('supplements/new/',             views.supplement_new,       name='supplement_new'),

    # Assign Diet
    path('assign/',                       views.assign_diet,          name='assign'),

    # Progress & History
    path('progress/<int:member_pk>/',    views.nutrition_progress,   name='progress'),
    path('history/<int:member_pk>/',     views.nutrition_history,    name='history'),
]
