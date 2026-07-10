from django.contrib import admin
from .models import (Department, Position, Role, Permission, Employee, Shift,
                      ShiftAssignment, EmployeeAttendance, Payroll, Bonus,
                      Deduction, LeaveRequest, PerformanceReview, Contract)

admin.site.register(Department)
admin.site.register(Position)
admin.site.register(Role)
admin.site.register(Permission)
admin.site.register(Shift)
admin.site.register(ShiftAssignment)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display  = ['employee_id','get_full_name','department','position','status','base_salary']
    list_filter   = ['status','department','employment_type']
    search_fields = ['first_name','last_name','email','employee_id']


@admin.register(EmployeeAttendance)
class EmployeeAttendanceAdmin(admin.ModelAdmin):
    list_display = ['employee','date','status']
    list_filter  = ['status','date']


@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ['employee','month','base_salary','net_salary','status']
    list_filter  = ['status']


admin.site.register(Bonus)
admin.site.register(Deduction)


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ['employee','leave_type','start_date','end_date','status']
    list_filter  = ['status','leave_type']


admin.site.register(PerformanceReview)
admin.site.register(Contract)
