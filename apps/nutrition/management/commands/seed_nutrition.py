"""python manage.py seed_nutrition"""
import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from apps.nutrition.models import FoodCategory, Food, Meal, NutritionPlan, NutritionLog, WaterIntake, Supplement
from apps.members.models import Member
from apps.coaches.models import Coach
from apps.accounts.models import User

FOOD_CATS = [('Proteins','fa-drumstick-bite','#EC4899'),('Carbs','fa-bread-slice','#F59E0B'),('Vegetables','fa-carrot','#10B981'),('Fruits','fa-apple-whole','#EF4444'),('Dairy','fa-bottle-water','#3B82F6'),('Fats','fa-droplet','#8B5CF6')]

FOODS = [
    ('Chicken Breast','Proteins',165,31,0,3.6,'g',100),
    ('Brown Rice','Carbs',216,5,45,1.8,'g',100),
    ('Broccoli','Vegetables',34,2.8,7,0.4,'g',100),
    ('Banana','Fruits',89,1.1,23,0.3,'pcs',1),
    ('Whole Eggs','Proteins',155,13,1.1,11,'pcs',2),
    ('Sweet Potato','Carbs',86,1.6,20,0.1,'g',100),
    ('Salmon','Proteins',208,20,0,13,'g',100),
    ('Greek Yogurt','Dairy',59,10,3.6,0.4,'g',100),
    ('Oats','Carbs',389,17,66,7,'g',100),
    ('Almonds','Fats',579,21,22,50,'g',30),
    ('Spinach','Vegetables',23,2.9,3.6,0.4,'g',100),
    ('Olive Oil','Fats',884,0,0,100,'tbsp',1),
    ('Whey Protein','Proteins',120,24,3,2,'g',30),
    ('Tuna','Proteins',116,26,0,1,'g',100),
    ('Apple','Fruits',52,0.3,14,0.2,'pcs',1),
]

MEALS = [
    ('High Protein Breakfast','breakfast','Scrambled eggs with veggies',500,35,40,18,5),
    ('Grilled Chicken Salad','lunch','Grilled chicken with mixed greens',420,40,20,15,15),
    ('Salmon & Rice','dinner','Baked salmon with brown rice',580,38,55,16,25),
    ('Pre-Workout Oats','pre_workout','Oats with banana and protein',380,25,55,8,8),
    ('Post-Workout Shake','post_workout','Whey protein with milk and banana',320,30,38,4,5),
    ('Turkey Wrap','lunch','Turkey with veggies in whole wheat wrap',450,32,42,12,10),
    ('Mixed Nuts Snack','snack','Trail mix with almonds and dried fruits',200,5,18,14,5),
]

class Command(BaseCommand):
    help = 'Seed nutrition demo data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\nSeeding nutrition...\n'))
        admin   = User.objects.filter(role='super_admin').first()
        members = list(Member.objects.all()[:12])
        coaches = list(Coach.objects.all())
        today   = date.today()

        cats = {}
        for name, icon, color in FOOD_CATS:
            c, _ = FoodCategory.objects.get_or_create(name=name, defaults={'icon':icon,'color':color})
            cats[name] = c

        for name, cat_name, cal, prot, carb, fat, unit, serving in FOODS:
            Food.objects.get_or_create(name=name, defaults={
                'category': cats.get(cat_name), 'calories': cal,
                'protein': prot, 'carbs': carb, 'fat': fat,
                'serving_unit': unit, 'serving_size': serving, 'created_by': admin,
            })

        for name, mtype, desc, cal, prot, carb, fat, prep in MEALS:
            Meal.objects.get_or_create(name=name, defaults={
                'meal_type': mtype, 'description': desc,
                'total_calories': cal, 'total_protein': prot,
                'total_carbs': carb, 'total_fat': fat,
                'prep_time_min': prep, 'created_by': admin,
            })

        created = 0
        for m in members[:8]:
            if NutritionPlan.objects.filter(member=m).exists(): continue
            coach = random.choice(coaches) if coaches else None
            goal  = random.choice(['weight_loss','muscle_gain','maintenance','health'])
            cal   = {'weight_loss':1600,'muscle_gain':2800,'maintenance':2100,'health':2000}.get(goal,2000)
            plan = NutritionPlan.objects.create(
                member=m, coach=coach,
                name=random.choice(['Cutting Plan','Bulk Plan','Clean Eating','Performance Diet']),
                goal=goal, daily_calories=cal,
                daily_protein=int(cal*0.3/4), daily_carbs=int(cal*0.4/4), daily_fat=int(cal*0.3/9),
                daily_water_ml=random.choice([2000,2500,3000]),
                start_date=today - timedelta(days=random.randint(7,45)),
                status='active', created_by=admin,
            )
            for days_ago in range(20,0,-1):
                d = today - timedelta(days=days_ago)
                if not NutritionLog.objects.filter(member=m, date=d).exists():
                    NutritionLog.objects.create(
                        member=m, date=d, calories_target=cal,
                        calories_actual=random.randint(int(cal*0.8), int(cal*1.1)),
                        protein_actual=random.uniform(80,180),
                        carbs_actual=random.uniform(100,300),
                        fat_actual=random.uniform(40,90),
                        water_ml=random.randint(1500,3000),
                    )
                WaterIntake.objects.get_or_create(member=m, date=d, defaults={'amount_ml': random.randint(200,2500)})
            created += 1

        # Supplements
        for m in random.sample(members, min(5, len(members))):
            Supplement.objects.get_or_create(member=m, name='Whey Protein', defaults={
                'brand':'Optimum Nutrition', 'dosage':'30g (1 scoop)',
                'frequency':'post_wo', 'start_date':today - timedelta(days=30),
            })

        self.stdout.write(self.style.SUCCESS(f'Done! {created} nutrition plans, {Food.objects.count()} foods, {Meal.objects.count()} meals seeded.'))
