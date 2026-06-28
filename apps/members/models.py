import qrcode
import io
import barcode
from barcode.writer import ImageWriter
from django.db import models
from django.utils import timezone
from django.core.files.base import ContentFile
from apps.accounts.models import User


# ── Member ─────────────────────────────────────────────────
class Member(models.Model):

    class Status(models.TextChoices):
        ACTIVE    = 'active',    'Active'
        INACTIVE  = 'inactive',  'Inactive'
        FROZEN    = 'frozen',    'Frozen'
        ARCHIVED  = 'archived',  'Archived'
        BLACKLIST = 'blacklist', 'Blacklisted'
        PENDING   = 'pending',   'Pending'

    class BloodType(models.TextChoices):
        A_POS  = 'A+',  'A+'
        A_NEG  = 'A-',  'A-'
        B_POS  = 'B+',  'B+'
        B_NEG  = 'B-',  'B-'
        AB_POS = 'AB+', 'AB+'
        AB_NEG = 'AB-', 'AB-'
        O_POS  = 'O+',  'O+'
        O_NEG  = 'O-',  'O-'
        UNKNOWN= '?',   'Unknown'

    class FitnessLevel(models.TextChoices):
        BEGINNER     = 'beginner',     'Beginner'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED     = 'advanced',     'Advanced'
        ELITE        = 'elite',        'Elite'

    # ── Core link ─────────────────────────────────────────
    user             = models.OneToOneField(User, on_delete=models.CASCADE,
                                            related_name='member_profile', null=True, blank=True)
    member_id        = models.CharField(max_length=20, unique=True, blank=True)

    # ── Personal ──────────────────────────────────────────
    first_name       = models.CharField(max_length=100)
    last_name        = models.CharField(max_length=100)
    email            = models.EmailField(blank=True)
    phone            = models.CharField(max_length=20, blank=True)
    phone_secondary  = models.CharField(max_length=20, blank=True)
    gender           = models.CharField(max_length=10,
                                        choices=User.Gender.choices, blank=True)
    birth_date       = models.DateField(null=True, blank=True)
    nationality      = models.CharField(max_length=60, blank=True)
    national_id      = models.CharField(max_length=30, blank=True)
    address          = models.TextField(blank=True)
    profile_image    = models.ImageField(upload_to='members/', null=True, blank=True)
    occupation       = models.CharField(max_length=100, blank=True)

    # ── Status ────────────────────────────────────────────
    status           = models.CharField(max_length=12, choices=Status.choices,
                                        default=Status.ACTIVE)
    join_date        = models.DateField(default=timezone.now)
    blacklist_reason = models.TextField(blank=True)
    freeze_start     = models.DateField(null=True, blank=True)
    freeze_end       = models.DateField(null=True, blank=True)
    freeze_reason    = models.TextField(blank=True)
    archived_at      = models.DateTimeField(null=True, blank=True)
    archive_reason   = models.TextField(blank=True)

    # ── Fitness ───────────────────────────────────────────
    fitness_level    = models.CharField(max_length=14, choices=FitnessLevel.choices,
                                        default=FitnessLevel.BEGINNER)
    blood_type       = models.CharField(max_length=4, choices=BloodType.choices,
                                        default=BloodType.UNKNOWN)

    # ── Assignments ───────────────────────────────────────
    assigned_coach       = models.ForeignKey(User, on_delete=models.SET_NULL,
                                             null=True, blank=True,
                                             related_name='coached_members',
                                             limit_choices_to={'role': 'coach'})
    assigned_nutritionist = models.ForeignKey(User, on_delete=models.SET_NULL,
                                              null=True, blank=True,
                                              related_name='nutritionist_members',
                                              limit_choices_to={'role': 'coach'})

    # ── QR / Barcode ──────────────────────────────────────
    qr_code          = models.ImageField(upload_to='members/qr/', null=True, blank=True)
    barcode_image    = models.ImageField(upload_to='members/barcode/', null=True, blank=True)

    # ── Merge tracking ────────────────────────────────────
    merged_into      = models.ForeignKey('self', on_delete=models.SET_NULL,
                                         null=True, blank=True,
                                         related_name='merged_from')

    # ── Meta ──────────────────────────────────────────────
    registered_by    = models.ForeignKey(User, on_delete=models.SET_NULL,
                                         null=True, blank=True,
                                         related_name='registered_members')
    notes            = models.TextField(blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table            = 'members'
        ordering            = ['-created_at']
        verbose_name        = 'Member'
        verbose_name_plural = 'Members'

    def __str__(self):
        return f"{self.get_full_name()} [{self.member_id}]"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_initials(self):
        parts = self.get_full_name().split()
        return ''.join(p[0].upper() for p in parts[:2]) if parts else '?'

    def get_age(self):
        if not self.birth_date:
            return None
        today = timezone.now().date()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    def get_status_color(self):
        return {
            'active':    'green',
            'inactive':  'gray',
            'frozen':    'blue',
            'archived':  'orange',
            'blacklist': 'red',
            'pending':   'orange',
        }.get(self.status, 'gray')

    def is_frozen(self):
        if self.status != self.Status.FROZEN:
            return False
        today = timezone.now().date()
        if self.freeze_end and today > self.freeze_end:
            return False
        return True

    def save(self, *args, **kwargs):
        # Auto-generate member_id
        if not self.member_id:
            last = Member.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.member_id = f"GYM{next_id:05d}"
        super().save(*args, **kwargs)

    def generate_qr(self):
        data = f"GYMX|{self.member_id}|{self.get_full_name()}|{self.email}"
        qr   = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(data)
        qr.make(fit=True)
        img    = qr.make_image(fill_color="#1D4ED8", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        fname = f"qr_{self.member_id}.png"
        self.qr_code.save(fname, ContentFile(buffer.getvalue()), save=False)

    def generate_barcode(self):
        try:
            code   = barcode.get('code128', self.member_id, writer=ImageWriter())
            buffer = io.BytesIO()
            code.write(buffer)
            fname  = f"barcode_{self.member_id}.png"
            self.barcode_image.save(fname, ContentFile(buffer.getvalue()), save=False)
        except Exception:
            pass  # barcode lib optional


# ── Emergency Contact ──────────────────────────────────────
class EmergencyContact(models.Model):
    class Relationship(models.TextChoices):
        PARENT   = 'parent',   'Parent'
        SPOUSE   = 'spouse',   'Spouse'
        SIBLING  = 'sibling',  'Sibling'
        FRIEND   = 'friend',   'Friend'
        DOCTOR   = 'doctor',   'Doctor'
        OTHER    = 'other',    'Other'

    member       = models.ForeignKey(Member, on_delete=models.CASCADE,
                                     related_name='emergency_contacts')
    name         = models.CharField(max_length=100)
    relationship = models.CharField(max_length=10, choices=Relationship.choices,
                                    default=Relationship.OTHER)
    phone        = models.CharField(max_length=20)
    phone_alt    = models.CharField(max_length=20, blank=True)
    email        = models.EmailField(blank=True)
    is_primary   = models.BooleanField(default=False)
    notes        = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  = 'members_emergency_contacts'
        ordering  = ['-is_primary', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_relationship_display()}) — {self.member.get_full_name()}"


# ── Medical Information ────────────────────────────────────
class MedicalInformation(models.Model):
    member              = models.OneToOneField(Member, on_delete=models.CASCADE,
                                               related_name='medical_info')
    blood_type          = models.CharField(max_length=4,
                                           choices=Member.BloodType.choices,
                                           default=Member.BloodType.UNKNOWN)
    height_cm           = models.DecimalField(max_digits=5, decimal_places=1,
                                              null=True, blank=True)
    weight_kg           = models.DecimalField(max_digits=5, decimal_places=1,
                                              null=True, blank=True)
    chronic_conditions  = models.TextField(blank=True)
    allergies           = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)
    past_surgeries      = models.TextField(blank=True)
    injuries            = models.TextField(blank=True)
    doctor_name         = models.CharField(max_length=100, blank=True)
    doctor_phone        = models.CharField(max_length=20, blank=True)
    medical_notes       = models.TextField(blank=True)
    last_updated        = models.DateTimeField(auto_now=True)
    updated_by          = models.ForeignKey(User, on_delete=models.SET_NULL,
                                            null=True, blank=True)

    class Meta:
        db_table = 'members_medical_info'

    def __str__(self):
        return f"Medical — {self.member.get_full_name()}"

    @property
    def bmi(self):
        if self.height_cm and self.weight_kg:
            h = float(self.height_cm) / 100
            return round(float(self.weight_kg) / (h * h), 1)
        return None

    @property
    def bmi_category(self):
        bmi = self.bmi
        if bmi is None:
            return '—'
        if bmi < 18.5:   return 'Underweight'
        if bmi < 25:     return 'Normal'
        if bmi < 30:     return 'Overweight'
        return 'Obese'


# ── Body Measurements ──────────────────────────────────────
class BodyMeasurement(models.Model):
    member       = models.ForeignKey(Member, on_delete=models.CASCADE,
                                     related_name='measurements')
    date         = models.DateField(default=timezone.now)
    weight_kg    = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    height_cm    = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    chest_cm     = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    waist_cm     = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    hips_cm      = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    bicep_cm     = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    thigh_cm     = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    calf_cm      = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    shoulder_cm  = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    neck_cm      = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    notes        = models.TextField(blank=True)
    recorded_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  = 'members_measurements'
        ordering  = ['-date']

    def __str__(self):
        return f"Measurements — {self.member.get_full_name()} — {self.date}"

    @property
    def bmi(self):
        if self.height_cm and self.weight_kg:
            h = float(self.height_cm) / 100
            return round(float(self.weight_kg) / (h * h), 1)
        return None


# ── Body Composition ───────────────────────────────────────
class BodyComposition(models.Model):
    member           = models.ForeignKey(Member, on_delete=models.CASCADE,
                                         related_name='body_compositions')
    date             = models.DateField(default=timezone.now)
    body_fat_pct     = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    muscle_mass_kg   = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    bone_mass_kg     = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    water_pct        = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    visceral_fat     = models.PositiveSmallIntegerField(null=True, blank=True)
    metabolic_age    = models.PositiveSmallIntegerField(null=True, blank=True)
    bmr_kcal         = models.PositiveIntegerField(null=True, blank=True)
    notes            = models.TextField(blank=True)
    recorded_by      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'members_body_composition'
        ordering = ['-date']

    def __str__(self):
        return f"Body Composition — {self.member.get_full_name()} — {self.date}"


# ── Progress Photo ─────────────────────────────────────────
class ProgressPhoto(models.Model):
    class View(models.TextChoices):
        FRONT = 'front', 'Front'
        SIDE  = 'side',  'Side'
        BACK  = 'back',  'Back'

    member     = models.ForeignKey(Member, on_delete=models.CASCADE,
                                   related_name='progress_photos')
    photo      = models.ImageField(upload_to='members/progress/')
    view       = models.CharField(max_length=6, choices=View.choices, default=View.FRONT)
    date       = models.DateField(default=timezone.now)
    weight_kg  = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    notes      = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'members_progress_photos'
        ordering = ['-date']

    def __str__(self):
        return f"Photo ({self.get_view_display()}) — {self.member.get_full_name()} — {self.date}"


# ── Member Document ────────────────────────────────────────
class MemberDocument(models.Model):
    class DocType(models.TextChoices):
        ID_COPY      = 'id',          'ID Copy'
        MEDICAL_CERT = 'medical',     'Medical Certificate'
        CONTRACT     = 'contract',    'Contract'
        PHOTO        = 'photo',       'Photo'
        OTHER        = 'other',       'Other'

    member      = models.ForeignKey(Member, on_delete=models.CASCADE,
                                    related_name='documents')
    title       = models.CharField(max_length=200)
    doc_type    = models.CharField(max_length=10, choices=DocType.choices,
                                   default=DocType.OTHER)
    file        = models.FileField(upload_to='members/documents/')
    notes       = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'members_documents'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} — {self.member.get_full_name()}"

    @property
    def file_ext(self):
        return self.file.name.split('.')[-1].upper() if self.file else '—'

    @property
    def file_size_kb(self):
        try:
            return round(self.file.size / 1024, 1)
        except Exception:
            return 0


# ── Member Note ────────────────────────────────────────────
class MemberNote(models.Model):
    class Priority(models.TextChoices):
        LOW    = 'low',    'Low'
        NORMAL = 'normal', 'Normal'
        HIGH   = 'high',   'High'
        URGENT = 'urgent', 'Urgent'

    member     = models.ForeignKey(Member, on_delete=models.CASCADE,
                                   related_name='member_notes')
    title      = models.CharField(max_length=200)
    body       = models.TextField()
    priority   = models.CharField(max_length=8, choices=Priority.choices,
                                  default=Priority.NORMAL)
    is_pinned  = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'members_notes'
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return f"[{self.priority}] {self.title} — {self.member.get_full_name()}"

    def get_priority_color(self):
        return {'low': 'gray', 'normal': 'blue',
                'high': 'orange', 'urgent': 'red'}.get(self.priority, 'gray')


# ── Member Goal ────────────────────────────────────────────
class MemberGoal(models.Model):
    class GoalType(models.TextChoices):
        WEIGHT_LOSS   = 'weight_loss',   'Weight Loss'
        MUSCLE_GAIN   = 'muscle_gain',   'Muscle Gain'
        ENDURANCE     = 'endurance',     'Endurance'
        FLEXIBILITY   = 'flexibility',   'Flexibility'
        STRENGTH      = 'strength',      'Strength'
        GENERAL_FIT   = 'general',       'General Fitness'
        REHABILITATION= 'rehab',         'Rehabilitation'

    class GoalStatus(models.TextChoices):
        IN_PROGRESS = 'in_progress', 'In Progress'
        ACHIEVED    = 'achieved',    'Achieved'
        PAUSED      = 'paused',      'Paused'
        CANCELLED   = 'cancelled',   'Cancelled'

    member       = models.ForeignKey(Member, on_delete=models.CASCADE,
                                     related_name='goals')
    goal_type    = models.CharField(max_length=20, choices=GoalType.choices)
    title        = models.CharField(max_length=200)
    description  = models.TextField(blank=True)
    target_value = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    current_value= models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    unit         = models.CharField(max_length=20, blank=True)
    target_date  = models.DateField(null=True, blank=True)
    status       = models.CharField(max_length=12, choices=GoalStatus.choices,
                                    default=GoalStatus.IN_PROGRESS)
    achieved_at  = models.DateField(null=True, blank=True)
    created_by   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'members_goals'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} — {self.member.get_full_name()}"

    @property
    def progress_pct(self):
        if self.target_value and self.current_value and float(self.target_value) > 0:
            return min(int(float(self.current_value) / float(self.target_value) * 100), 100)
        return 0

    def get_status_color(self):
        return {'in_progress': 'blue', 'achieved': 'green',
                'paused': 'orange', 'cancelled': 'gray'}.get(self.status, 'gray')


# ── Member Timeline Event ──────────────────────────────────
class MemberTimeline(models.Model):
    class EventType(models.TextChoices):
        JOINED         = 'joined',          'Joined'
        MEMBERSHIP_NEW = 'membership_new',  'New Membership'
        MEMBERSHIP_RNW = 'membership_rnw',  'Membership Renewed'
        MEMBERSHIP_EXP = 'membership_exp',  'Membership Expired'
        PAYMENT        = 'payment',         'Payment'
        ATTENDANCE     = 'attendance',      'Checked In'
        GOAL_ACHIEVED  = 'goal_achieved',   'Goal Achieved'
        COACH_ASSIGNED = 'coach_assigned',  'Coach Assigned'
        NOTE           = 'note',            'Note Added'
        FROZEN         = 'frozen',          'Account Frozen'
        UNFROZEN       = 'unfrozen',        'Account Unfrozen'
        MEASUREMENT    = 'measurement',     'Measurement Recorded'
        DOCUMENT       = 'document',        'Document Added'
        STATUS_CHANGE  = 'status_change',   'Status Changed'

    member      = models.ForeignKey(Member, on_delete=models.CASCADE,
                                    related_name='timeline')
    event_type  = models.CharField(max_length=20, choices=EventType.choices)
    title       = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date        = models.DateTimeField(default=timezone.now)
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'members_timeline'
        ordering = ['-date']

    def __str__(self):
        return f"{self.event_type} — {self.member.get_full_name()} — {self.date:%Y-%m-%d}"

    def get_icon(self):
        icons = {
            'joined':          'fa-user-plus',
            'membership_new':  'fa-id-card',
            'membership_rnw':  'fa-rotate',
            'membership_exp':  'fa-calendar-xmark',
            'payment':         'fa-credit-card',
            'attendance':      'fa-calendar-check',
            'goal_achieved':   'fa-trophy',
            'coach_assigned':  'fa-person-running',
            'note':            'fa-note-sticky',
            'frozen':          'fa-snowflake',
            'unfrozen':        'fa-sun',
            'measurement':     'fa-ruler',
            'document':        'fa-file',
            'status_change':   'fa-circle-dot',
        }
        return icons.get(self.event_type, 'fa-circle-dot')

    def get_color(self):
        colors = {
            'joined':          'blue',
            'membership_new':  'green',
            'membership_rnw':  'green',
            'membership_exp':  'red',
            'payment':         'green',
            'attendance':      'blue',
            'goal_achieved':   'orange',
            'coach_assigned':  'purple',
            'note':            'gray',
            'frozen':          'blue',
            'unfrozen':        'green',
            'measurement':     'gray',
            'document':        'gray',
            'status_change':   'orange',
        }
        return colors.get(self.event_type, 'gray')
