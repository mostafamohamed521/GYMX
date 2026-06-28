from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST

from .models import (
    Member, EmergencyContact, MedicalInformation,
    BodyMeasurement, BodyComposition, ProgressPhoto,
    MemberDocument, MemberNote, MemberGoal, MemberTimeline,
)
from .forms import (
    MemberForm, EmergencyContactForm, MedicalInfoForm,
    BodyMeasurementForm, BodyCompositionForm, ProgressPhotoForm,
    MemberDocumentForm, MemberNoteForm, MemberGoalForm,
    AssignCoachForm, FreezeMemberForm, TransferMemberForm,
    BlacklistMemberForm, MergeMembersForm, MemberSearchForm,
)
from apps.accounts.utils import log_activity


def _log(request, action, desc):
    log_activity(request, request.user, action, desc)


def _timeline(member, event_type, title, desc='', user=None):
    MemberTimeline.objects.create(
        member=member, event_type=event_type,
        title=title, description=desc, created_by=user,
    )


# ── Members List ───────────────────────────────────────────
@login_required
def member_list(request):
    form    = MemberSearchForm(request.GET)
    members = Member.objects.select_related('assigned_coach')

    if form.is_valid():
        q  = form.cleaned_data.get('q', '').strip()
        st = form.cleaned_data.get('status')
        fl = form.cleaned_data.get('fitness_level')
        gn = form.cleaned_data.get('gender')
        if q:
            members = members.filter(
                Q(first_name__icontains=q) | Q(last_name__icontains=q) |
                Q(email__icontains=q)      | Q(phone__icontains=q)     |
                Q(member_id__icontains=q)
            )
        if st:  members = members.filter(status=st)
        if fl:  members = members.filter(fitness_level=fl)
        if gn:  members = members.filter(gender=gn)

    stats = {
        'total':     Member.objects.count(),
        'active':    Member.objects.filter(status='active').count(),
        'frozen':    Member.objects.filter(status='frozen').count(),
        'archived':  Member.objects.filter(status='archived').count(),
        'blacklist': Member.objects.filter(status='blacklist').count(),
    }
    return render(request, 'members/member_list.html', {
        'members': members,
        'form':    form,
        'stats':   stats,
    })


# ── Add Member ─────────────────────────────────────────────
@login_required
def member_add(request):
    if request.method == 'POST':
        form = MemberForm(request.POST, request.FILES)
        if form.is_valid():
            member = form.save(commit=False)
            member.registered_by = request.user
            member.save()
            member.generate_qr()
            member.save(update_fields=['qr_code'])
            _timeline(member, 'joined', 'Member joined GymX', user=request.user)
            _log(request, 'member_added', f'Added member: {member.get_full_name()}')
            messages.success(request, f'Member {member.get_full_name()} added successfully!')
            return redirect('members:detail', pk=member.pk)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = MemberForm()
    return render(request, 'members/member_form.html', {
        'form': form, 'action': 'Add', 'page_title': 'Add Member',
    })


# ── Member Detail ──────────────────────────────────────────
@login_required
def member_detail(request, pk):
    member = get_object_or_404(Member, pk=pk)
    latest_measurement  = member.measurements.first()
    latest_composition  = member.body_compositions.first()
    recent_notes        = member.member_notes.all()[:3]
    active_goals        = member.goals.filter(status='in_progress')[:3]
    emergency_contacts  = member.emergency_contacts.all()
    recent_photos       = member.progress_photos.all()[:3]
    documents           = member.documents.all()[:5]
    timeline_events     = member.timeline.all()[:10]

    try:
        medical = member.medical_info
    except MedicalInformation.DoesNotExist:
        medical = None

    return render(request, 'members/member_detail.html', {
        'member':             member,
        'latest_measurement': latest_measurement,
        'latest_composition': latest_composition,
        'recent_notes':       recent_notes,
        'active_goals':       active_goals,
        'emergency_contacts': emergency_contacts,
        'recent_photos':      recent_photos,
        'documents':          documents,
        'timeline_events':    timeline_events,
        'medical':            medical,
    })


# ── Edit Member ────────────────────────────────────────────
@login_required
def member_edit(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        form = MemberForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()
            _timeline(member, 'status_change', 'Member profile updated', user=request.user)
            _log(request, 'member_updated', f'Updated member: {member.get_full_name()}')
            messages.success(request, 'Member updated successfully!')
            return redirect('members:detail', pk=pk)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = MemberForm(instance=member)
    return render(request, 'members/member_form.html', {
        'form': form, 'member': member,
        'action': 'Edit', 'page_title': f'Edit — {member.get_full_name()}',
    })


# ── Delete Member ──────────────────────────────────────────
@login_required
def member_delete(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        name = member.get_full_name()
        member.delete()
        _log(request, 'member_updated', f'Deleted member: {name}')
        messages.success(request, f'Member {name} deleted.')
        return redirect('members:list')
    return render(request, 'members/member_delete.html', {'member': member})


# ── Archive / Restore ──────────────────────────────────────
@login_required
def member_archive(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        member.status      = Member.Status.ARCHIVED
        member.archived_at = timezone.now()
        member.archive_reason = reason
        member.save(update_fields=['status','archived_at','archive_reason'])
        _timeline(member, 'status_change', 'Member archived', desc=reason, user=request.user)
        messages.success(request, f'{member.get_full_name()} archived.')
        return redirect('members:list')
    return render(request, 'members/member_archive.html', {'member': member})


@login_required
def member_restore(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        member.status      = Member.Status.ACTIVE
        member.archived_at = None
        member.archive_reason = ''
        member.save(update_fields=['status','archived_at','archive_reason'])
        _timeline(member, 'status_change', 'Member restored', user=request.user)
        messages.success(request, f'{member.get_full_name()} restored to active.')
        return redirect('members:detail', pk=pk)
    return render(request, 'members/member_restore.html', {'member': member})


# ── Freeze Member ──────────────────────────────────────────
@login_required
def member_freeze(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        form = FreezeMemberForm(request.POST, instance=member)
        if form.is_valid():
            m = form.save(commit=False)
            m.status = Member.Status.FROZEN
            m.save()
            _timeline(member, 'frozen',
                      f"Account frozen until {m.freeze_end}",
                      desc=m.freeze_reason, user=request.user)
            messages.success(request, f'{member.get_full_name()} frozen successfully.')
            return redirect('members:detail', pk=pk)
    else:
        form = FreezeMemberForm(instance=member)
    return render(request, 'members/member_freeze.html', {'form': form, 'member': member})


@login_required
def member_unfreeze(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        member.status       = Member.Status.ACTIVE
        member.freeze_start = None
        member.freeze_end   = None
        member.freeze_reason = ''
        member.save(update_fields=['status','freeze_start','freeze_end','freeze_reason'])
        _timeline(member, 'unfrozen', 'Account unfrozen', user=request.user)
        messages.success(request, f'{member.get_full_name()} unfrozen.')
        return redirect('members:detail', pk=pk)
    return render(request, 'members/member_unfreeze.html', {'member': member})


# ── Blacklist ──────────────────────────────────────────────
@login_required
def member_blacklist(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        form = BlacklistMemberForm(request.POST, instance=member)
        if form.is_valid():
            m = form.save(commit=False)
            m.status = Member.Status.BLACKLIST
            m.save()
            _timeline(member, 'status_change', 'Member blacklisted',
                      desc=m.blacklist_reason, user=request.user)
            messages.warning(request, f'{member.get_full_name()} has been blacklisted.')
            return redirect('members:list')
    else:
        form = BlacklistMemberForm(instance=member)
    return render(request, 'members/member_blacklist.html', {'form': form, 'member': member})


# ── Transfer ───────────────────────────────────────────────
@login_required
def member_transfer(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        form = TransferMemberForm(request.POST)
        if form.is_valid():
            branch = form.cleaned_data['target_branch']
            reason = form.cleaned_data['reason']
            _timeline(member, 'status_change',
                      f"Transferred to {branch}", reason, request.user)
            messages.success(request, f'{member.get_full_name()} transfer recorded.')
            return redirect('members:detail', pk=pk)
    else:
        form = TransferMemberForm()
    return render(request, 'members/member_transfer.html', {'form': form, 'member': member})


# ── Merge Members ──────────────────────────────────────────
@login_required
def member_merge(request):
    if request.method == 'POST':
        form = MergeMembersForm(request.POST)
        if form.is_valid():
            primary   = form.cleaned_data['primary_member']
            duplicate = form.cleaned_data['duplicate_member']
            duplicate.merged_into = primary
            duplicate.status = Member.Status.ARCHIVED
            duplicate.save(update_fields=['merged_into','status'])
            _timeline(primary, 'status_change',
                      f"Merged with {duplicate.get_full_name()} [{duplicate.member_id}]",
                      user=request.user)
            messages.success(request, 'Members merged successfully.')
            return redirect('members:detail', pk=primary.pk)
    else:
        form = MergeMembersForm()
    return render(request, 'members/member_merge.html', {'form': form})


# ── Timeline ───────────────────────────────────────────────
@login_required
def member_timeline_view(request, pk):
    member = get_object_or_404(Member, pk=pk)
    events = member.timeline.select_related('created_by').all()
    return render(request, 'members/member_timeline.html', {
        'member': member, 'events': events,
    })


# ── Notes ──────────────────────────────────────────────────
@login_required
def member_notes(request, pk):
    member = get_object_or_404(Member, pk=pk)
    notes  = member.member_notes.all()
    if request.method == 'POST':
        form = MemberNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.member     = member
            note.created_by = request.user
            note.save()
            _timeline(member, 'note', f"Note added: {note.title}", user=request.user)
            messages.success(request, 'Note added.')
            return redirect('members:notes', pk=pk)
    else:
        form = MemberNoteForm()
    return render(request, 'members/member_notes.html', {
        'member': member, 'notes': notes, 'form': form,
    })


@login_required
def member_note_delete(request, pk, note_pk):
    member = get_object_or_404(Member, pk=pk)
    note   = get_object_or_404(MemberNote, pk=note_pk, member=member)
    note.delete()
    messages.success(request, 'Note deleted.')
    return redirect('members:notes', pk=pk)


# ── Medical Information ────────────────────────────────────
@login_required
def member_medical(request, pk):
    member = get_object_or_404(Member, pk=pk)
    medical, _ = MedicalInformation.objects.get_or_create(member=member)
    if request.method == 'POST':
        form = MedicalInfoForm(request.POST, instance=medical)
        if form.is_valid():
            m = form.save(commit=False)
            m.updated_by = request.user
            m.save()
            messages.success(request, 'Medical information updated.')
            return redirect('members:medical', pk=pk)
    else:
        form = MedicalInfoForm(instance=medical)
    return render(request, 'members/member_medical.html', {
        'member': member, 'medical': medical, 'form': form,
    })


# ── Emergency Contacts ─────────────────────────────────────
@login_required
def member_emergency(request, pk):
    member   = get_object_or_404(Member, pk=pk)
    contacts = member.emergency_contacts.all()
    if request.method == 'POST':
        form = EmergencyContactForm(request.POST)
        if form.is_valid():
            c = form.save(commit=False)
            c.member = member
            c.save()
            messages.success(request, 'Emergency contact added.')
            return redirect('members:emergency', pk=pk)
    else:
        form = EmergencyContactForm()
    return render(request, 'members/member_emergency.html', {
        'member': member, 'contacts': contacts, 'form': form,
    })


@login_required
def emergency_contact_delete(request, pk, contact_pk):
    member  = get_object_or_404(Member, pk=pk)
    contact = get_object_or_404(EmergencyContact, pk=contact_pk, member=member)
    contact.delete()
    messages.success(request, 'Contact removed.')
    return redirect('members:emergency', pk=pk)


# ── Body Measurements ──────────────────────────────────────
@login_required
def member_measurements(request, pk):
    member       = get_object_or_404(Member, pk=pk)
    measurements = member.measurements.all()
    if request.method == 'POST':
        form = BodyMeasurementForm(request.POST)
        if form.is_valid():
            m = form.save(commit=False)
            m.member      = member
            m.recorded_by = request.user
            m.save()
            _timeline(member, 'measurement',
                      f"Measurements recorded — Weight: {m.weight_kg}kg",
                      user=request.user)
            messages.success(request, 'Measurements saved.')
            return redirect('members:measurements', pk=pk)
    else:
        form = BodyMeasurementForm()
    return render(request, 'members/member_measurements.html', {
        'member': member, 'measurements': measurements, 'form': form,
    })


# ── Body Composition ───────────────────────────────────────
@login_required
def member_composition(request, pk):
    member       = get_object_or_404(Member, pk=pk)
    compositions = member.body_compositions.all()
    if request.method == 'POST':
        form = BodyCompositionForm(request.POST)
        if form.is_valid():
            c = form.save(commit=False)
            c.member      = member
            c.recorded_by = request.user
            c.save()
            messages.success(request, 'Body composition saved.')
            return redirect('members:composition', pk=pk)
    else:
        form = BodyCompositionForm()
    return render(request, 'members/member_composition.html', {
        'member': member, 'compositions': compositions, 'form': form,
    })


# ── Progress Photos ────────────────────────────────────────
@login_required
def member_photos(request, pk):
    member = get_object_or_404(Member, pk=pk)
    photos = member.progress_photos.all()
    if request.method == 'POST':
        form = ProgressPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            p = form.save(commit=False)
            p.member = member
            p.save()
            messages.success(request, 'Progress photo uploaded.')
            return redirect('members:photos', pk=pk)
    else:
        form = ProgressPhotoForm()
    return render(request, 'members/member_photos.html', {
        'member': member, 'photos': photos, 'form': form,
    })


@login_required
def member_photo_delete(request, pk, photo_pk):
    member = get_object_or_404(Member, pk=pk)
    photo  = get_object_or_404(ProgressPhoto, pk=photo_pk, member=member)
    photo.delete()
    messages.success(request, 'Photo deleted.')
    return redirect('members:photos', pk=pk)


# ── Documents ──────────────────────────────────────────────
@login_required
def member_documents(request, pk):
    member    = get_object_or_404(Member, pk=pk)
    documents = member.documents.all()
    if request.method == 'POST':
        form = MemberDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            d = form.save(commit=False)
            d.member      = member
            d.uploaded_by = request.user
            d.save()
            _timeline(member, 'document', f"Document added: {d.title}", user=request.user)
            messages.success(request, 'Document uploaded.')
            return redirect('members:documents', pk=pk)
    else:
        form = MemberDocumentForm()
    return render(request, 'members/member_documents.html', {
        'member': member, 'documents': documents, 'form': form,
    })


@login_required
def member_document_delete(request, pk, doc_pk):
    member = get_object_or_404(Member, pk=pk)
    doc    = get_object_or_404(MemberDocument, pk=doc_pk, member=member)
    doc.delete()
    messages.success(request, 'Document deleted.')
    return redirect('members:documents', pk=pk)


# ── Assign Coach / Nutritionist ────────────────────────────
@login_required
def member_assign(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        form = AssignCoachForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            if member.assigned_coach:
                _timeline(member, 'coach_assigned',
                          f"Coach assigned: {member.assigned_coach.get_full_name()}",
                          user=request.user)
            messages.success(request, 'Assignments updated.')
            return redirect('members:detail', pk=pk)
    else:
        form = AssignCoachForm(instance=member)
    return render(request, 'members/member_assign.html', {
        'member': member, 'form': form,
    })


# ── Goals ──────────────────────────────────────────────────
@login_required
def member_goals(request, pk):
    member = get_object_or_404(Member, pk=pk)
    goals  = member.goals.all()
    if request.method == 'POST':
        form = MemberGoalForm(request.POST)
        if form.is_valid():
            g = form.save(commit=False)
            g.member     = member
            g.created_by = request.user
            g.save()
            messages.success(request, 'Goal added.')
            return redirect('members:goals', pk=pk)
    else:
        form = MemberGoalForm()
    return render(request, 'members/member_goals.html', {
        'member': member, 'goals': goals, 'form': form,
    })


@login_required
def member_goal_achieve(request, pk, goal_pk):
    member = get_object_or_404(Member, pk=pk)
    goal   = get_object_or_404(MemberGoal, pk=goal_pk, member=member)
    goal.status      = MemberGoal.GoalStatus.ACHIEVED
    goal.achieved_at = timezone.now().date()
    goal.save(update_fields=['status','achieved_at'])
    _timeline(member, 'goal_achieved', f"Goal achieved: {goal.title}", user=request.user)
    messages.success(request, f'Goal "{goal.title}" marked as achieved!')
    return redirect('members:goals', pk=pk)


@login_required
def member_goal_delete(request, pk, goal_pk):
    member = get_object_or_404(Member, pk=pk)
    goal   = get_object_or_404(MemberGoal, pk=goal_pk, member=member)
    goal.delete()
    messages.success(request, 'Goal deleted.')
    return redirect('members:goals', pk=pk)


# ── QR Code & Barcode ──────────────────────────────────────
@login_required
def member_qr(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if not member.qr_code:
        member.generate_qr()
        member.save(update_fields=['qr_code'])
    return render(request, 'members/member_qr.html', {'member': member})


@login_required
def member_barcode(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if not member.barcode_image:
        member.generate_barcode()
        member.save(update_fields=['barcode_image'])
    return render(request, 'members/member_barcode.html', {'member': member})


# ── Member Card ────────────────────────────────────────────
@login_required
def member_card(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if not member.qr_code:
        member.generate_qr()
        member.save(update_fields=['qr_code'])
    return render(request, 'members/member_card.html', {'member': member})


# ── History stubs (linked to future sprints) ───────────────
@login_required
def member_membership_history(request, pk):
    member = get_object_or_404(Member, pk=pk)
    return render(request, 'members/member_history.html', {
        'member': member, 'history_type': 'Membership',
        'icon': 'fa-id-card', 'color': 'blue',
        'message': 'Membership history will be available after Sprint 3 (Memberships module).',
    })


@login_required
def member_attendance_history(request, pk):
    member = get_object_or_404(Member, pk=pk)
    return render(request, 'members/member_history.html', {
        'member': member, 'history_type': 'Attendance',
        'icon': 'fa-calendar-check', 'color': 'green',
        'message': 'Attendance history will be available after Sprint 5 (Attendance module).',
    })


@login_required
def member_payment_history(request, pk):
    member = get_object_or_404(Member, pk=pk)
    return render(request, 'members/member_history.html', {
        'member': member, 'history_type': 'Payment',
        'icon': 'fa-credit-card', 'color': 'orange',
        'message': 'Payment history will be available after Sprint 4 (Payments module).',
    })


@login_required
def member_workout_history(request, pk):
    member = get_object_or_404(Member, pk=pk)
    return render(request, 'members/member_history.html', {
        'member': member, 'history_type': 'Workout',
        'icon': 'fa-dumbbell', 'color': 'purple',
        'message': 'Workout history will be available after Sprint 6 (Classes module).',
    })


@login_required
def member_nutrition_history(request, pk):
    member = get_object_or_404(Member, pk=pk)
    return render(request, 'members/member_history.html', {
        'member': member, 'history_type': 'Nutrition',
        'icon': 'fa-bowl-food', 'color': 'green',
        'message': 'Nutrition history will be available in a future sprint.',
    })
