from django import forms
from .models import (
    Member, EmergencyContact, MedicalInformation,
    BodyMeasurement, BodyComposition, ProgressPhoto,
    MemberDocument, MemberNote, MemberGoal
)

_c  = 'form-control'
_s  = 'form-select'
_f  = 'form-control'
_ta = 'form-control'


class MemberForm(forms.ModelForm):
    class Meta:
        model  = Member
        fields = [
            'first_name','last_name','email','phone','phone_secondary',
            'gender','birth_date','nationality','national_id','address',
            'profile_image','occupation','fitness_level','blood_type',
            'join_date','status','notes',
        ]
        widgets = {
            'first_name':      forms.TextInput(attrs={'class':_c,'placeholder':'First name'}),
            'last_name':       forms.TextInput(attrs={'class':_c,'placeholder':'Last name'}),
            'email':           forms.EmailInput(attrs={'class':_c,'placeholder':'Email address'}),
            'phone':           forms.TextInput(attrs={'class':_c,'placeholder':'+20 1XX XXX XXXX'}),
            'phone_secondary': forms.TextInput(attrs={'class':_c,'placeholder':'Secondary phone'}),
            'gender':          forms.Select(attrs={'class':_s}),
            'birth_date':      forms.DateInput(attrs={'class':_c,'type':'date'}),
            'nationality':     forms.TextInput(attrs={'class':_c,'placeholder':'Nationality'}),
            'national_id':     forms.TextInput(attrs={'class':_c,'placeholder':'National ID / Passport'}),
            'address':         forms.Textarea(attrs={'class':_ta,'rows':2,'placeholder':'Full address'}),
            'profile_image':   forms.FileInput(attrs={'class':_f,'accept':'image/*'}),
            'occupation':      forms.TextInput(attrs={'class':_c,'placeholder':'Occupation'}),
            'fitness_level':   forms.Select(attrs={'class':_s}),
            'blood_type':      forms.Select(attrs={'class':_s}),
            'join_date':       forms.DateInput(attrs={'class':_c,'type':'date'}),
            'status':          forms.Select(attrs={'class':_s}),
            'notes':           forms.Textarea(attrs={'class':_ta,'rows':2,'placeholder':'Internal notes...'}),
        }


class EmergencyContactForm(forms.ModelForm):
    class Meta:
        model  = EmergencyContact
        fields = ['name','relationship','phone','phone_alt','email','is_primary','notes']
        widgets = {
            'name':         forms.TextInput(attrs={'class':_c,'placeholder':'Full name'}),
            'relationship': forms.Select(attrs={'class':_s}),
            'phone':        forms.TextInput(attrs={'class':_c,'placeholder':'+20 1XX XXX XXXX'}),
            'phone_alt':    forms.TextInput(attrs={'class':_c,'placeholder':'Alternative phone'}),
            'email':        forms.EmailInput(attrs={'class':_c,'placeholder':'Email'}),
            'notes':        forms.Textarea(attrs={'class':_ta,'rows':2}),
        }


class MedicalInfoForm(forms.ModelForm):
    class Meta:
        model  = MedicalInformation
        fields = [
            'blood_type','height_cm','weight_kg',
            'chronic_conditions','allergies','current_medications',
            'past_surgeries','injuries','doctor_name','doctor_phone','medical_notes',
        ]
        widgets = {
            'blood_type':          forms.Select(attrs={'class':_s}),
            'height_cm':           forms.NumberInput(attrs={'class':_c,'placeholder':'e.g. 175','step':'0.1'}),
            'weight_kg':           forms.NumberInput(attrs={'class':_c,'placeholder':'e.g. 70','step':'0.1'}),
            'chronic_conditions':  forms.Textarea(attrs={'class':_ta,'rows':2,'placeholder':'e.g. Diabetes, Hypertension'}),
            'allergies':           forms.Textarea(attrs={'class':_ta,'rows':2,'placeholder':'e.g. Penicillin, Latex'}),
            'current_medications': forms.Textarea(attrs={'class':_ta,'rows':2,'placeholder':'List current medications'}),
            'past_surgeries':      forms.Textarea(attrs={'class':_ta,'rows':2,'placeholder':'Past surgical history'}),
            'injuries':            forms.Textarea(attrs={'class':_ta,'rows':2,'placeholder':'Current or past injuries'}),
            'doctor_name':         forms.TextInput(attrs={'class':_c,'placeholder':'Doctor name'}),
            'doctor_phone':        forms.TextInput(attrs={'class':_c,'placeholder':'Doctor phone'}),
            'medical_notes':       forms.Textarea(attrs={'class':_ta,'rows':2,'placeholder':'Additional notes'}),
        }


class BodyMeasurementForm(forms.ModelForm):
    class Meta:
        model  = BodyMeasurement
        fields = [
            'date','weight_kg','height_cm',
            'chest_cm','waist_cm','hips_cm',
            'bicep_cm','thigh_cm','calf_cm',
            'shoulder_cm','neck_cm','notes',
        ]
        widgets = {
            'date':        forms.DateInput(attrs={'class':_c,'type':'date'}),
            'weight_kg':   forms.NumberInput(attrs={'class':_c,'placeholder':'kg','step':'0.1'}),
            'height_cm':   forms.NumberInput(attrs={'class':_c,'placeholder':'cm','step':'0.1'}),
            'chest_cm':    forms.NumberInput(attrs={'class':_c,'placeholder':'cm','step':'0.1'}),
            'waist_cm':    forms.NumberInput(attrs={'class':_c,'placeholder':'cm','step':'0.1'}),
            'hips_cm':     forms.NumberInput(attrs={'class':_c,'placeholder':'cm','step':'0.1'}),
            'bicep_cm':    forms.NumberInput(attrs={'class':_c,'placeholder':'cm','step':'0.1'}),
            'thigh_cm':    forms.NumberInput(attrs={'class':_c,'placeholder':'cm','step':'0.1'}),
            'calf_cm':     forms.NumberInput(attrs={'class':_c,'placeholder':'cm','step':'0.1'}),
            'shoulder_cm': forms.NumberInput(attrs={'class':_c,'placeholder':'cm','step':'0.1'}),
            'neck_cm':     forms.NumberInput(attrs={'class':_c,'placeholder':'cm','step':'0.1'}),
            'notes':       forms.Textarea(attrs={'class':_ta,'rows':2}),
        }


class BodyCompositionForm(forms.ModelForm):
    class Meta:
        model  = BodyComposition
        fields = [
            'date','body_fat_pct','muscle_mass_kg','bone_mass_kg',
            'water_pct','visceral_fat','metabolic_age','bmr_kcal','notes',
        ]
        widgets = {
            'date':           forms.DateInput(attrs={'class':_c,'type':'date'}),
            'body_fat_pct':   forms.NumberInput(attrs={'class':_c,'placeholder':'%','step':'0.1'}),
            'muscle_mass_kg': forms.NumberInput(attrs={'class':_c,'placeholder':'kg','step':'0.1'}),
            'bone_mass_kg':   forms.NumberInput(attrs={'class':_c,'placeholder':'kg','step':'0.1'}),
            'water_pct':      forms.NumberInput(attrs={'class':_c,'placeholder':'%','step':'0.1'}),
            'visceral_fat':   forms.NumberInput(attrs={'class':_c,'placeholder':'1-20'}),
            'metabolic_age':  forms.NumberInput(attrs={'class':_c,'placeholder':'years'}),
            'bmr_kcal':       forms.NumberInput(attrs={'class':_c,'placeholder':'kcal'}),
            'notes':          forms.Textarea(attrs={'class':_ta,'rows':2}),
        }


class ProgressPhotoForm(forms.ModelForm):
    class Meta:
        model  = ProgressPhoto
        fields = ['photo','view','date','weight_kg','notes']
        widgets = {
            'photo':     forms.FileInput(attrs={'class':_f,'accept':'image/*'}),
            'view':      forms.Select(attrs={'class':_s}),
            'date':      forms.DateInput(attrs={'class':_c,'type':'date'}),
            'weight_kg': forms.NumberInput(attrs={'class':_c,'placeholder':'kg','step':'0.1'}),
            'notes':     forms.Textarea(attrs={'class':_ta,'rows':2}),
        }


class MemberDocumentForm(forms.ModelForm):
    class Meta:
        model  = MemberDocument
        fields = ['title','doc_type','file','notes']
        widgets = {
            'title':    forms.TextInput(attrs={'class':_c,'placeholder':'Document title'}),
            'doc_type': forms.Select(attrs={'class':_s}),
            'file':     forms.FileInput(attrs={'class':_f}),
            'notes':    forms.Textarea(attrs={'class':_ta,'rows':2}),
        }


class MemberNoteForm(forms.ModelForm):
    class Meta:
        model  = MemberNote
        fields = ['title','body','priority','is_pinned']
        widgets = {
            'title':     forms.TextInput(attrs={'class':_c,'placeholder':'Note title'}),
            'body':      forms.Textarea(attrs={'class':_ta,'rows':4,'placeholder':'Write your note...'}),
            'priority':  forms.Select(attrs={'class':_s}),
        }


class MemberGoalForm(forms.ModelForm):
    class Meta:
        model  = MemberGoal
        fields = ['goal_type','title','description','target_value','current_value','unit','target_date','status']
        widgets = {
            'goal_type':     forms.Select(attrs={'class':_s}),
            'title':         forms.TextInput(attrs={'class':_c,'placeholder':'Goal title'}),
            'description':   forms.Textarea(attrs={'class':_ta,'rows':2,'placeholder':'Describe this goal'}),
            'target_value':  forms.NumberInput(attrs={'class':_c,'placeholder':'Target value','step':'0.01'}),
            'current_value': forms.NumberInput(attrs={'class':_c,'placeholder':'Current value','step':'0.01'}),
            'unit':          forms.TextInput(attrs={'class':_c,'placeholder':'e.g. kg, minutes'}),
            'target_date':   forms.DateInput(attrs={'class':_c,'type':'date'}),
            'status':        forms.Select(attrs={'class':_s}),
        }


class AssignCoachForm(forms.ModelForm):
    class Meta:
        model  = Member
        fields = ['assigned_coach','assigned_nutritionist']
        widgets = {
            'assigned_coach':       forms.Select(attrs={'class':_s}),
            'assigned_nutritionist':forms.Select(attrs={'class':_s}),
        }


class FreezeMemberForm(forms.ModelForm):
    class Meta:
        model  = Member
        fields = ['freeze_start','freeze_end','freeze_reason']
        widgets = {
            'freeze_start':  forms.DateInput(attrs={'class':'form-control','type':'date'}),
            'freeze_end':    forms.DateInput(attrs={'class':'form-control','type':'date'}),
            'freeze_reason': forms.Textarea(attrs={'class':'form-control','rows':3,'placeholder':'Reason for freezing...'}),
        }


class TransferMemberForm(forms.Form):
    target_branch = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Target branch name'}),
        label='Target Branch'
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'class':'form-control','rows':3,'placeholder':'Transfer reason'}),
        label='Reason'
    )
    transfer_date = forms.DateField(
        widget=forms.DateInput(attrs={'class':'form-control','type':'date'}),
        label='Transfer Date'
    )


class BlacklistMemberForm(forms.ModelForm):
    class Meta:
        model  = Member
        fields = ['blacklist_reason']
        widgets = {
            'blacklist_reason': forms.Textarea(attrs={
                'class':'form-control','rows':4,
                'placeholder':'Provide a detailed reason for blacklisting this member...'
            }),
        }


class MergeMembersForm(forms.Form):
    primary_member = forms.ModelChoiceField(
        queryset=Member.objects.filter(status='active'),
        widget=forms.Select(attrs={'class':'form-select'}),
        label='Primary Member (keep this one)',
        help_text='The data from the duplicate will be merged into this member.'
    )
    duplicate_member = forms.ModelChoiceField(
        queryset=Member.objects.filter(status='active'),
        widget=forms.Select(attrs={'class':'form-select'}),
        label='Duplicate Member (will be archived)',
    )
    confirm = forms.BooleanField(
        label='I confirm this action is irreversible',
        required=True
    )

    def clean(self):
        cd = super().clean()
        p  = cd.get('primary_member')
        d  = cd.get('duplicate_member')
        if p and d and p == d:
            raise forms.ValidationError('Primary and duplicate members cannot be the same.')
        return cd


class MemberSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class':'form-control',
            'placeholder':'Search by name, email, phone, or member ID...',
            'id':'memberSearch',
        })
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('','All Statuses')] + list(Member.Status.choices),
        widget=forms.Select(attrs={'class':'form-select'})
    )
    fitness_level = forms.ChoiceField(
        required=False,
        choices=[('','All Levels')] + list(Member.FitnessLevel.choices),
        widget=forms.Select(attrs={'class':'form-select'})
    )
    gender = forms.ChoiceField(
        required=False,
        choices=[('','All Genders'),(('male','Male')),('female','Female')],
        widget=forms.Select(attrs={'class':'form-select'})
    )
