from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator

User = get_user_model()

_cls  = 'form-control'
_sel  = 'form-select'
_file = 'form-control'

def _w(widget, placeholder='', extra=None):
    attrs = {'class': _cls, 'placeholder': placeholder}
    if extra:
        attrs.update(extra)
    return widget(attrs=attrs)


# ── Login ──────────────────────────────────────────────────
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': _cls, 'placeholder': 'Enter your username', 'autofocus': True}))
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': _cls, 'placeholder': 'Enter your password', 'id': 'password-field'}))
    remember_me = forms.BooleanField(required=False)


# ── Member Registration ────────────────────────────────────
class MemberRegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': _cls, 'placeholder': 'Create a password', 'id': 'pw1'}))
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': _cls, 'placeholder': 'Confirm password'}))

    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'username', 'email', 'phone', 'gender', 'birth_date']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': _cls, 'placeholder': 'First name'}),
            'last_name':  forms.TextInput(attrs={'class': _cls, 'placeholder': 'Last name'}),
            'username':   forms.TextInput(attrs={'class': _cls, 'placeholder': 'Choose a username'}),
            'email':      forms.EmailInput(attrs={'class': _cls, 'placeholder': 'Email address'}),
            'phone':      forms.TextInput(attrs={'class': _cls, 'placeholder': '+20 1XX XXX XXXX'}),
            'gender':     forms.Select(attrs={'class': _sel}),
            'birth_date': forms.DateInput(attrs={'class': _cls, 'type': 'date'}),
        }

    def clean(self):
        cd = super().clean()
        p1, p2 = cd.get('password1'), cd.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return cd

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.role = User.Role.MEMBER
        if commit:
            user.save()
        return user


# ── Staff Registration ─────────────────────────────────────
class StaffRegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': _cls, 'placeholder': 'Create a password', 'id': 'pw1-staff'}))
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': _cls, 'placeholder': 'Confirm password'}))

    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'username', 'email', 'phone', 'gender', 'role']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': _cls, 'placeholder': 'First name'}),
            'last_name':  forms.TextInput(attrs={'class': _cls, 'placeholder': 'Last name'}),
            'username':   forms.TextInput(attrs={'class': _cls, 'placeholder': 'Choose a username'}),
            'email':      forms.EmailInput(attrs={'class': _cls, 'placeholder': 'Email address'}),
            'phone':      forms.TextInput(attrs={'class': _cls, 'placeholder': '+20 1XX XXX XXXX'}),
            'gender':     forms.Select(attrs={'class': _sel}),
            'role':       forms.Select(attrs={'class': _sel}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only staff-level roles
        self.fields['role'].choices = [
            (User.Role.GYM_MANAGER,  'Gym Manager'),
            (User.Role.RECEPTIONIST, 'Receptionist'),
            (User.Role.COACH,        'Coach'),
        ]

    def clean(self):
        cd = super().clean()
        p1, p2 = cd.get('password1'), cd.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return cd

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.is_staff = True
        if commit:
            user.save()
        return user


# ── Complete Registration ──────────────────────────────────
class CompleteRegistrationForm(forms.ModelForm):
    class Meta:
        model  = User
        fields = ['profile_image', 'address', 'bio', 'emergency_contact_name', 'emergency_contact_phone']
        widgets = {
            'profile_image':          forms.FileInput(attrs={'class': _file, 'accept': 'image/*'}),
            'address':                forms.Textarea(attrs={'class': _cls, 'rows': 3, 'placeholder': 'Full address'}),
            'bio':                    forms.Textarea(attrs={'class': _cls, 'rows': 2, 'placeholder': 'Short bio (optional)'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': _cls, 'placeholder': 'Emergency contact name'}),
            'emergency_contact_phone':forms.TextInput(attrs={'class': _cls, 'placeholder': '+20 1XX XXX XXXX'}),
        }


# ── OTP Verification ───────────────────────────────────────
class OTPVerifyForm(forms.Form):
    otp = forms.CharField(
        max_length=6, min_length=6,
        widget=forms.TextInput(attrs={
            'class': _cls,
            'placeholder': '000000',
            'maxlength': '6',
            'inputmode': 'numeric',
            'autocomplete': 'one-time-code',
            'style': 'letter-spacing:14px;font-size:24px;text-align:center;font-weight:700;',
        }),
        label='Verification Code'
    )


# ── Profile Update ─────────────────────────────────────────
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'gender',
                  'birth_date', 'address', 'profile_image', 'bio',
                  'emergency_contact_name', 'emergency_contact_phone']
        widgets = {
            'first_name':   forms.TextInput(attrs={'class': _cls, 'placeholder': 'First name'}),
            'last_name':    forms.TextInput(attrs={'class': _cls, 'placeholder': 'Last name'}),
            'email':        forms.EmailInput(attrs={'class': _cls, 'placeholder': 'Email address'}),
            'phone':        forms.TextInput(attrs={'class': _cls, 'placeholder': '+20 1XX XXX XXXX'}),
            'gender':       forms.Select(attrs={'class': _sel}),
            'birth_date':   forms.DateInput(attrs={'class': _cls, 'type': 'date'}),
            'address':      forms.Textarea(attrs={'class': _cls, 'rows': 3}),
            'profile_image':forms.FileInput(attrs={'class': _file, 'accept': 'image/*'}),
            'bio':          forms.Textarea(attrs={'class': _cls, 'rows': 3}),
            'emergency_contact_name':  forms.TextInput(attrs={'class': _cls, 'placeholder': 'Name'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': _cls, 'placeholder': '+20 1XX XXX XXXX'}),
        }


# ── Password Change ────────────────────────────────────────
class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': _cls, 'placeholder': 'Current password'}),
        label='Current Password')
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': _cls, 'placeholder': 'New password', 'id': 'pw-new1'}),
        label='New Password')
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': _cls, 'placeholder': 'Confirm new password'}),
        label='Confirm New Password')


# ── Forgot Password ────────────────────────────────────────
class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': _cls, 'placeholder': 'Enter your registered email'}),
        label='Email Address')


# ── Reset Password ─────────────────────────────────────────
class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={'class': _cls, 'placeholder': 'New password', 'id': 'pw-reset1'}),
        label='New Password')
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': _cls, 'placeholder': 'Confirm new password'}),
        label='Confirm Password')

    def clean(self):
        cd = super().clean()
        p1, p2 = cd.get('new_password'), cd.get('confirm_password')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return cd


# ── User Preferences ──────────────────────────────────────
class UserPreferencesForm(forms.ModelForm):
    class Meta:
        model  = User
        fields = ['theme', 'language', 'notif_email', 'notif_sms', 'notif_push',
                  'notif_payment', 'notif_membership', 'notif_attendance']
        widgets = {
            'theme':    forms.Select(attrs={'class': _sel}),
            'language': forms.Select(attrs={'class': _sel}),
        }
