from django.db import models
from django.utils import timezone
from apps.accounts.models import User


class SavedReport(models.Model):
    class ReportType(models.TextChoices):
        REVENUE     = 'revenue',     'Revenue'
        MEMBERSHIP  = 'membership',  'Membership'
        ATTENDANCE  = 'attendance',  'Attendance'
        PAYMENTS    = 'payments',    'Payments'
        COACHES     = 'coaches',     'Coaches'
        EMPLOYEES   = 'employees',   'Employees'
        INVENTORY   = 'inventory',   'Inventory'
        SALES       = 'sales',       'Sales'
        CUSTOM      = 'custom',      'Custom'

    name        = models.CharField(max_length=200)
    report_type = models.CharField(max_length=12, choices=ReportType.choices, default=ReportType.CUSTOM)
    date_from   = models.DateField(null=True, blank=True)
    date_to     = models.DateField(null=True, blank=True)
    filters     = models.JSONField(default=dict, blank=True)
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'saved_reports'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class ExportLog(models.Model):
    class Format(models.TextChoices):
        PDF = 'pdf', 'PDF'
        CSV = 'csv', 'CSV'
        XLSX = 'xlsx', 'Excel'

    class Status(models.TextChoices):
        PENDING   = 'pending',   'Pending'
        COMPLETED = 'completed', 'Completed'
        FAILED    = 'failed',    'Failed'

    report_name = models.CharField(max_length=200)
    format      = models.CharField(max_length=5, choices=Format.choices, default=Format.PDF)
    status      = models.CharField(max_length=10, choices=Status.choices, default=Status.COMPLETED)
    requested_by= models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'export_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.report_name} ({self.format})"

    def get_status_color(self):
        return {'pending':'orange','completed':'green','failed':'red'}.get(self.status,'gray')

    def get_format_icon(self):
        return {'pdf':'fa-file-pdf','csv':'fa-file-csv','xlsx':'fa-file-excel'}.get(self.format,'fa-file')
