from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q

from .models import LoginHistory, Notification, ActivityLog, UserSession
from .forms import (
    LoginForm, MemberRegisterForm, StaffRegisterForm,
    CompleteRegistrationForm, OTPVerifyForm,
    ProfileUpdateForm, CustomPasswordChangeForm,
    ForgotPasswordForm, ResetPasswordForm, UserPreferencesForm,
)
from .utils import log_login, log_activity, create_notification, track_session, get_client_ip

User = get_user_model()


# ── Splash / Welcome ──────────────────────────────────────
def splash_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    return render(request, 'public/splash.html')


def welcome_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    return render(request, 'public/welcome.html')


# ── Login / Logout ─────────────────────────────────────────
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()

            if user.is_account_locked:
                messages.error(request, 'Account is temporarily locked. Please try again later.')
                log_login(request, user, 'locked')
                return render(request, 'authentication/login.html', {'form': form})

            login(request, user)

            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)
            else:
                request.session.set_expiry(1209600)

            user.last_login_ip = get_client_ip(request)
            user.failed_login_count = 0
            user.save(update_fields=['last_login_ip', 'failed_login_count'])

            log_login(request, user, 'success')
            log_activity(request, user, 'login', 'Logged in successfully')
            track_session(request, user)

            messages.success(request, f'Welcome back, {user.get_short_name()}!')
            return redirect(request.GET.get('next', 'dashboard:index'))
        else:
            # Track failed attempts
            username = request.POST.get('username', '')
            try:
                u = User.objects.get(username=username)
                u.failed_login_count += 1
                if u.failed_login_count >= 5:
                    u.locked_until = timezone.now() + timezone.timedelta(minutes=15)
                    messages.error(request, 'Too many failed attempts. Account locked for 15 minutes.')
                else:
                    messages.error(request, f'Invalid credentials. {5 - u.failed_login_count} attempts remaining.')
                u.save(update_fields=['failed_login_count', 'locked_until'])
                log_login(request, u, 'failed')
            except User.DoesNotExist:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()

    return render(request, 'authentication/login.html', {'form': form})


def logout_view(request):
    if request.user.is_authenticated:
        log_activity(request, request.user, 'logout', 'Logged out')
        log_login(request, request.user, 'logout')
        UserSession.objects.filter(
            session_key=request.session.session_key
        ).update(is_active=False)
    logout(request)
    messages.info(request, 'You have been signed out.')
    return redirect('accounts:login')


# ── Registration ───────────────────────────────────────────
def register_member_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    if request.method == 'POST':
        form = MemberRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            otp  = user.generate_otp()
            request.session['verify_user_id'] = user.pk
            request.session['verify_type']    = 'email'
            log_activity(request, user, 'register', 'New member registered')
            create_notification(user, 'success', 'Welcome to GymX!',
                                'Your account has been created. Please verify your email.')
            messages.success(request, 'Account created! Please verify your email.')
            return redirect('accounts:email_verification')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = MemberRegisterForm()
    return render(request, 'authentication/register_member.html', {'form': form})


@login_required
def register_staff_view(request):
    if not request.user.can_manage_members:
        messages.error(request, 'You do not have permission to add staff.')
        return redirect('dashboard:index')
    if request.method == 'POST':
        form = StaffRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            log_activity(request, request.user, 'member_added',
                         f'Staff member added: {user.get_full_name()} ({user.get_role_display()})')
            messages.success(request, f'Staff member {user.get_full_name()} added successfully!')
            return redirect('dashboard:index')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = StaffRegisterForm()
    return render(request, 'authentication/register_staff.html', {'form': form})


@login_required
def complete_registration_view(request):
    if request.method == 'POST':
        form = CompleteRegistrationForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            log_activity(request, request.user, 'profile_update', 'Completed registration')
            messages.success(request, 'Registration completed!')
            return redirect('dashboard:index')
    else:
        form = CompleteRegistrationForm(instance=request.user)
    return render(request, 'authentication/complete_registration.html', {'form': form})


# ── Email Verification ─────────────────────────────────────
def email_verification_view(request):
    user_id = request.session.get('verify_user_id')
    if not user_id:
        return redirect('accounts:login')
    user = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        form = OTPVerifyForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            if user.is_otp_valid(otp, 'email'):
                user.is_email_verified = True
                user.clear_otp()
                user.save(update_fields=['is_email_verified'])
                log_activity(request, user, 'email_verified', 'Email verified successfully')
                login(request, user)
                del request.session['verify_user_id']
                messages.success(request, 'Email verified! Welcome to GymX.')
                return redirect('accounts:complete_registration')
            else:
                messages.error(request, 'Invalid or expired code. Please try again.')
    else:
        form = OTPVerifyForm()

    return render(request, 'authentication/email_verification.html', {
        'form': form,
        'email': user.email,
        'masked_email': _mask_email(user.email),
    })


def resend_otp_view(request):
    user_id = request.session.get('verify_user_id')
    if user_id:
        user = get_object_or_404(User, pk=user_id)
        user.generate_otp()
        messages.success(request, 'A new code has been sent.')
    return redirect('accounts:email_verification')


# ── Phone OTP ──────────────────────────────────────────────
@login_required
def phone_otp_view(request):
    user = request.user
    if request.method == 'POST':
        form = OTPVerifyForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            if user.is_otp_valid(otp, 'phone'):
                user.is_phone_verified = True
                user.clear_otp()
                user.save(update_fields=['is_phone_verified'])
                log_activity(request, user, 'phone_verified', 'Phone verified successfully')
                messages.success(request, 'Phone number verified!')
                return redirect('accounts:profile')
            else:
                messages.error(request, 'Invalid or expired code.')
    else:
        user.generate_otp()
        form = OTPVerifyForm()

    return render(request, 'authentication/phone_otp.html', {
        'form': form,
        'masked_phone': _mask_phone(user.phone),
    })


# ── Forgot / Reset Password ────────────────────────────────
def forgot_password_view(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                u = User.objects.get(email=email)
                otp = u.generate_otp()
                request.session['reset_user_id'] = u.pk
            except User.DoesNotExist:
                pass
            messages.success(request, 'If that email exists, a reset code has been sent.')
            return redirect('accounts:reset_password', token='verify')
    else:
        form = ForgotPasswordForm()
    return render(request, 'authentication/forgot_password.html', {'form': form})


def reset_password_view(request, token=None):
    user_id = request.session.get('reset_user_id')
    if not user_id:
        return redirect('accounts:forgot_password')
    user = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['new_password'])
            user.save()
            user.clear_otp()
            del request.session['reset_user_id']
            log_activity(request, user, 'password_change', 'Password reset via email')
            messages.success(request, 'Password reset successfully. Please sign in.')
            return redirect('accounts:login')
    else:
        form = ResetPasswordForm()
    return render(request, 'authentication/reset_password.html', {'form': form})


# ── Password Change ────────────────────────────────────────
@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            log_activity(request, user, 'password_change', 'Password changed')
            messages.success(request, 'Password changed successfully!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'authentication/change_password.html', {'form': form})


# ── 2FA ───────────────────────────────────────────────────
@login_required
def two_fa_view(request):
    user = request.user
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'enable':
            user.two_fa_enabled = True
            user.save(update_fields=['two_fa_enabled'])
            log_activity(request, user, '2fa_enabled', '2FA enabled')
            messages.success(request, 'Two-Factor Authentication enabled!')
        elif action == 'disable':
            user.two_fa_enabled = False
            user.save(update_fields=['two_fa_enabled'])
            log_activity(request, user, '2fa_disabled', '2FA disabled')
            messages.info(request, 'Two-Factor Authentication disabled.')
        return redirect('accounts:two_fa')
    return render(request, 'authentication/two_fa.html')


# ── Profile ────────────────────────────────────────────────
@login_required
def profile_view(request):
    stats = {
        'login_count': request.user.login_history.filter(status='success').count(),
        'last_password_change': request.user.login_history.filter(
            status='success').order_by('-created_at').first(),
    }
    return render(request, 'authentication/profile.html', {'stats': stats})


@login_required
def profile_edit_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            log_activity(request, request.user, 'profile_update', 'Profile updated')
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'authentication/profile_edit.html', {'form': form})


# ── User Preferences ──────────────────────────────────────
@login_required
def preferences_view(request):
    if request.method == 'POST':
        form = UserPreferencesForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            log_activity(request, request.user, 'settings_change', 'Preferences updated')
            messages.success(request, 'Preferences saved!')
            return redirect('accounts:preferences')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = UserPreferencesForm(instance=request.user)
    return render(request, 'authentication/preferences.html', {'form': form})


# ── Sessions ───────────────────────────────────────────────
@login_required
def session_management_view(request):
    sessions = UserSession.objects.filter(user=request.user, is_active=True)
    current_key = request.session.session_key
    return render(request, 'authentication/session_management.html', {
        'sessions':    sessions,
        'current_key': current_key,
    })


@login_required
def revoke_session_view(request, session_id):
    session = get_object_or_404(UserSession, pk=session_id, user=request.user)
    session.is_active = False
    session.save()
    messages.success(request, 'Session revoked.')
    return redirect('accounts:session_management')


@login_required
def revoke_all_sessions_view(request):
    if request.method == 'POST':
        UserSession.objects.filter(
            user=request.user, is_active=True
        ).exclude(
            session_key=request.session.session_key
        ).update(is_active=False)
        messages.success(request, 'All other sessions have been revoked.')
    return redirect('accounts:session_management')


# ── Login History ──────────────────────────────────────────
@login_required
def login_history_view(request):
    history = LoginHistory.objects.filter(user=request.user)[:50]
    return render(request, 'authentication/login_history.html', {'history': history})


# ── Notifications ──────────────────────────────────────────
@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user)
    unread_count  = notifications.filter(is_read=False).count()
    # Mark all as read when page is opened
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'authentication/notifications.html', {
        'notifications': notifications,
        'unread_count':  unread_count,
    })


@login_required
def mark_notification_read_view(request, pk):
    n = get_object_or_404(Notification, pk=pk, user=request.user)
    n.is_read = True
    n.save()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok'})
    return redirect('accounts:notifications')


@login_required
def clear_all_notifications_view(request):
    if request.method == 'POST':
        Notification.objects.filter(user=request.user).delete()
        messages.success(request, 'All notifications cleared.')
    return redirect('accounts:notifications')


# ── Activity Log ───────────────────────────────────────────
@login_required
def activity_log_view(request):
    logs = ActivityLog.objects.filter(user=request.user)
    filter_action = request.GET.get('action', '')
    if filter_action:
        logs = logs.filter(action=filter_action)
    return render(request, 'authentication/activity_log.html', {
        'logs':          logs[:100],
        'filter_action': filter_action,
        'action_choices': ActivityLog.Action.choices,
    })


# ── Helpers ────────────────────────────────────────────────
def _mask_email(email):
    try:
        local, domain = email.split('@')
        masked = local[0] + '*' * (len(local) - 2) + local[-1] if len(local) > 2 else local[0] + '*'
        return f"{masked}@{domain}"
    except Exception:
        return email


def _mask_phone(phone):
    if not phone or len(phone) < 4:
        return phone
    return phone[:3] + '*' * (len(phone) - 6) + phone[-3:]
