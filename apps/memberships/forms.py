from django import forms
from django.utils import timezone
from .models import (
    MembershipCategory, MembershipPlan, MemberSubscription,
    Discount, Coupon, Offer, FamilyMembership, CorporateMembership,
    FamilyMember, CorporateEmployee,
)
from apps.members.models import Member

_c = 'form-control'
_s = 'form-select'


class MembershipCategoryForm(forms.ModelForm):
    class Meta:
        model  = MembershipCategory
        fields = ['name', 'description', 'color', 'icon', 'is_active', 'sort_order']
        widgets = {
            'name':        forms.TextInput(attrs={'class': _c, 'placeholder': 'Category name'}),
            'description': forms.Textarea(attrs={'class': _c, 'rows': 2}),
            'color':       forms.TextInput(attrs={'class': _c, 'type': 'color', 'style': 'height:42px;padding:4px 8px;'}),
            'icon':        forms.TextInput(attrs={'class': _c, 'placeholder': 'e.g. fa-dumbbell'}),
            'sort_order':  forms.NumberInput(attrs={'class': _c}),
        }


class MembershipPlanForm(forms.ModelForm):
    features_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': _c, 'rows': 5,
            'placeholder': 'One feature per line:\nFull gym access\nLocker room\n2 guest passes/month',
        }),
        label='Features (one per line)',
        help_text='Each line becomes a feature bullet point'
    )

    class Meta:
        model  = MembershipPlan
        fields = [
            'category', 'name', 'plan_type', 'billing_cycle',
            'duration_days', 'price', 'setup_fee', 'max_freeze_days',
            'max_members', 'description', 'is_active', 'is_featured',
            'is_public', 'sort_order',
        ]
        widgets = {
            'category':      forms.Select(attrs={'class': _s}),
            'name':          forms.TextInput(attrs={'class': _c, 'placeholder': 'Plan name'}),
            'plan_type':     forms.Select(attrs={'class': _s}),
            'billing_cycle': forms.Select(attrs={'class': _s}),
            'duration_days': forms.NumberInput(attrs={'class': _c, 'placeholder': '30'}),
            'price':         forms.NumberInput(attrs={'class': _c, 'placeholder': '0.00', 'step': '0.01'}),
            'setup_fee':     forms.NumberInput(attrs={'class': _c, 'placeholder': '0.00', 'step': '0.01'}),
            'max_freeze_days': forms.NumberInput(attrs={'class': _c}),
            'max_members':   forms.NumberInput(attrs={'class': _c, 'placeholder': 'Leave blank for unlimited'}),
            'description':   forms.Textarea(attrs={'class': _c, 'rows': 3}),
            'sort_order':    forms.NumberInput(attrs={'class': _c}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.features:
            self.fields['features_text'].initial = '\n'.join(self.instance.features)

    def save(self, commit=True):
        instance = super().save(commit=False)
        raw = self.cleaned_data.get('features_text', '')
        instance.features = [
            line.strip() for line in raw.splitlines() if line.strip()
        ]
        if commit:
            instance.save()
        return instance


class SubscriptionForm(forms.ModelForm):
    coupon_code = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': _c, 'placeholder': 'Enter coupon code'}),
        label='Coupon Code'
    )

    class Meta:
        model  = MemberSubscription
        fields = [
            'member', 'plan', 'start_date', 'end_date',
            'payment_status', 'amount_paid', 'auto_renew', 'notes',
        ]
        widgets = {
            'member':         forms.Select(attrs={'class': _s}),
            'plan':           forms.Select(attrs={'class': _s}),
            'start_date':     forms.DateInput(attrs={'class': _c, 'type': 'date'}),
            'end_date':       forms.DateInput(attrs={'class': _c, 'type': 'date'}),
            'payment_status': forms.Select(attrs={'class': _s}),
            'amount_paid':    forms.NumberInput(attrs={'class': _c, 'step': '0.01'}),
            'notes':          forms.Textarea(attrs={'class': _c, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['member'].queryset = Member.objects.filter(
            status='active'
        ).order_by('first_name')


class RenewSubscriptionForm(forms.Form):
    plan = forms.ModelChoiceField(
        queryset=MembershipPlan.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': _s}),
        label='Renewal Plan'
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': _c, 'type': 'date'}),
        initial=timezone.now().date,
        label='Start Date'
    )
    payment_status = forms.ChoiceField(
        choices=MemberSubscription.PaymentStatus.choices,
        widget=forms.Select(attrs={'class': _s}),
        label='Payment Status'
    )
    amount_paid = forms.DecimalField(
        max_digits=10, decimal_places=2, required=False,
        widget=forms.NumberInput(attrs={'class': _c, 'step': '0.01'}),
        label='Amount Paid'
    )
    coupon_code = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': _c, 'placeholder': 'Coupon code (optional)'}),
        label='Coupon Code'
    )
    auto_renew = forms.BooleanField(required=False, label='Enable Auto-Renew')
    notes      = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': _c, 'rows': 2}),
        label='Notes'
    )


class UpgradeSubscriptionForm(forms.Form):
    new_plan = forms.ModelChoiceField(
        queryset=MembershipPlan.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': _s}),
        label='New Plan'
    )
    effective_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': _c, 'type': 'date'}),
        initial=timezone.now().date,
        label='Effective Date'
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': _c, 'rows': 2}),
    )


class TransferSubscriptionForm(forms.Form):
    target_member = forms.ModelChoiceField(
        queryset=Member.objects.filter(status='active'),
        widget=forms.Select(attrs={'class': _s}),
        label='Transfer To Member'
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'class': _c, 'rows': 3}),
        label='Reason for Transfer'
    )


class FreezeSubscriptionForm(forms.Form):
    freeze_start = forms.DateField(
        widget=forms.DateInput(attrs={'class': _c, 'type': 'date'}),
        initial=timezone.now().date,
        label='Freeze Start'
    )
    freeze_end = forms.DateField(
        widget=forms.DateInput(attrs={'class': _c, 'type': 'date'}),
        label='Freeze End'
    )
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': _c, 'rows': 2}),
        label='Reason'
    )

    def clean(self):
        cd = super().clean()
        fs = cd.get('freeze_start')
        fe = cd.get('freeze_end')
        if fs and fe and fe <= fs:
            raise forms.ValidationError('Freeze end must be after freeze start.')
        return cd


class DiscountForm(forms.ModelForm):
    class Meta:
        model  = Discount
        fields = [
            'name', 'discount_type', 'value', 'max_discount',
            'applicable_plans', 'valid_from', 'valid_until',
            'usage_limit', 'is_active', 'description',
        ]
        widgets = {
            'name':             forms.TextInput(attrs={'class': _c, 'placeholder': 'Discount name'}),
            'discount_type':    forms.Select(attrs={'class': _s}),
            'value':            forms.NumberInput(attrs={'class': _c, 'step': '0.01'}),
            'max_discount':     forms.NumberInput(attrs={'class': _c, 'step': '0.01'}),
            'applicable_plans': forms.SelectMultiple(attrs={'class': _c, 'size': '5'}),
            'valid_from':       forms.DateInput(attrs={'class': _c, 'type': 'date'}),
            'valid_until':      forms.DateInput(attrs={'class': _c, 'type': 'date'}),
            'usage_limit':      forms.NumberInput(attrs={'class': _c}),
            'description':      forms.Textarea(attrs={'class': _c, 'rows': 2}),
        }


class CouponForm(forms.ModelForm):
    class Meta:
        model  = Coupon
        fields = ['code', 'discount', 'member', 'is_single_use',
                  'valid_until', 'is_active']
        widgets = {
            'code':         forms.TextInput(attrs={'class': _c, 'placeholder': 'e.g. SUMMER25', 'style': 'text-transform:uppercase;'}),
            'discount':     forms.Select(attrs={'class': _s}),
            'member':       forms.Select(attrs={'class': _s}),
            'valid_until':  forms.DateInput(attrs={'class': _c, 'type': 'date'}),
        }

    def clean_code(self):
        return self.cleaned_data['code'].upper().strip()


class OfferForm(forms.ModelForm):
    class Meta:
        model  = Offer
        fields = [
            'name', 'offer_type', 'description', 'discount',
            'applicable_plans', 'banner_image',
            'valid_from', 'valid_until', 'is_active', 'is_featured',
        ]
        widgets = {
            'name':             forms.TextInput(attrs={'class': _c, 'placeholder': 'Offer name'}),
            'offer_type':       forms.Select(attrs={'class': _s}),
            'description':      forms.Textarea(attrs={'class': _c, 'rows': 3}),
            'discount':         forms.Select(attrs={'class': _s}),
            'applicable_plans': forms.SelectMultiple(attrs={'class': _c, 'size': '4'}),
            'banner_image':     forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'valid_from':       forms.DateInput(attrs={'class': _c, 'type': 'date'}),
            'valid_until':      forms.DateInput(attrs={'class': _c, 'type': 'date'}),
        }


class FamilyMembershipForm(forms.ModelForm):
    class Meta:
        model  = FamilyMembership
        fields = ['name', 'primary_member', 'plan', 'max_members', 'discount_per_member']
        widgets = {
            'name':                 forms.TextInput(attrs={'class': _c}),
            'primary_member':       forms.Select(attrs={'class': _s}),
            'plan':                 forms.Select(attrs={'class': _s}),
            'max_members':          forms.NumberInput(attrs={'class': _c}),
            'discount_per_member':  forms.NumberInput(attrs={'class': _c, 'step': '0.01'}),
        }


class CorporateMembershipForm(forms.ModelForm):
    class Meta:
        model  = CorporateMembership
        fields = [
            'company_name', 'company_email', 'company_phone', 'company_address',
            'contact_person', 'plan', 'max_employees', 'discount_pct',
            'contract_start', 'contract_end', 'is_active', 'notes',
        ]
        widgets = {
            'company_name':    forms.TextInput(attrs={'class': _c}),
            'company_email':   forms.EmailInput(attrs={'class': _c}),
            'company_phone':   forms.TextInput(attrs={'class': _c}),
            'company_address': forms.Textarea(attrs={'class': _c, 'rows': 2}),
            'contact_person':  forms.TextInput(attrs={'class': _c}),
            'plan':            forms.Select(attrs={'class': _s}),
            'max_employees':   forms.NumberInput(attrs={'class': _c}),
            'discount_pct':    forms.NumberInput(attrs={'class': _c, 'step': '0.01'}),
            'contract_start':  forms.DateInput(attrs={'class': _c, 'type': 'date'}),
            'contract_end':    forms.DateInput(attrs={'class': _c, 'type': 'date'}),
            'notes':           forms.Textarea(attrs={'class': _c, 'rows': 2}),
        }
