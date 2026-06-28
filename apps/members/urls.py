from django.urls import path
from . import views

app_name = 'members'

urlpatterns = [
    # Core CRUD
    path('',                    views.member_list,    name='list'),
    path('add/',                views.member_add,     name='add'),
    path('<int:pk>/',           views.member_detail,  name='detail'),
    path('<int:pk>/edit/',      views.member_edit,    name='edit'),
    path('<int:pk>/delete/',    views.member_delete,  name='delete'),

    # Status Actions
    path('<int:pk>/archive/',   views.member_archive,   name='archive'),
    path('<int:pk>/restore/',   views.member_restore,   name='restore'),
    path('<int:pk>/freeze/',    views.member_freeze,    name='freeze'),
    path('<int:pk>/unfreeze/',  views.member_unfreeze,  name='unfreeze'),
    path('<int:pk>/blacklist/', views.member_blacklist, name='blacklist'),
    path('<int:pk>/transfer/',  views.member_transfer,  name='transfer'),
    path('merge/',              views.member_merge,     name='merge'),

    # Profile Sections
    path('<int:pk>/timeline/',       views.member_timeline_view, name='timeline'),
    path('<int:pk>/notes/',          views.member_notes,         name='notes'),
    path('<int:pk>/notes/<int:note_pk>/delete/', views.member_note_delete, name='note_delete'),
    path('<int:pk>/medical/',        views.member_medical,       name='medical'),
    path('<int:pk>/emergency/',      views.member_emergency,     name='emergency'),
    path('<int:pk>/emergency/<int:contact_pk>/delete/', views.emergency_contact_delete, name='emergency_delete'),
    path('<int:pk>/measurements/',   views.member_measurements,  name='measurements'),
    path('<int:pk>/composition/',    views.member_composition,   name='composition'),
    path('<int:pk>/photos/',         views.member_photos,        name='photos'),
    path('<int:pk>/photos/<int:photo_pk>/delete/', views.member_photo_delete, name='photo_delete'),
    path('<int:pk>/documents/',      views.member_documents,     name='documents'),
    path('<int:pk>/documents/<int:doc_pk>/delete/', views.member_document_delete, name='document_delete'),
    path('<int:pk>/assign/',         views.member_assign,        name='assign'),
    path('<int:pk>/goals/',          views.member_goals,         name='goals'),
    path('<int:pk>/goals/<int:goal_pk>/achieve/', views.member_goal_achieve, name='goal_achieve'),
    path('<int:pk>/goals/<int:goal_pk>/delete/',  views.member_goal_delete,  name='goal_delete'),

    # Cards & Codes
    path('<int:pk>/qr/',      views.member_qr,      name='qr'),
    path('<int:pk>/barcode/', views.member_barcode, name='barcode'),
    path('<int:pk>/card/',    views.member_card,    name='card'),

    # History (future sprints)
    path('<int:pk>/history/memberships/', views.member_membership_history, name='membership_history'),
    path('<int:pk>/history/attendance/',  views.member_attendance_history, name='attendance_history'),
    path('<int:pk>/history/payments/',    views.member_payment_history,    name='payment_history'),
    path('<int:pk>/history/workouts/',    views.member_workout_history,    name='workout_history'),
    path('<int:pk>/history/nutrition/',   views.member_nutrition_history,  name='nutrition_history'),
]
