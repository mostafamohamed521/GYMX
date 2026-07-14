from django.contrib import admin
from .models import Branch, BranchSettings, MemberTransfer, EmployeeTransfer


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name','code','city','status','manager','is_main_branch']
    list_filter  = ['status','is_main_branch']
    search_fields= ['name','code','city']


admin.site.register(BranchSettings)


@admin.register(MemberTransfer)
class MemberTransferAdmin(admin.ModelAdmin):
    list_display = ['member','from_branch','to_branch','status','requested_at']
    list_filter  = ['status']


@admin.register(EmployeeTransfer)
class EmployeeTransferAdmin(admin.ModelAdmin):
    list_display = ['employee','from_branch','to_branch','status','requested_at']
    list_filter  = ['status']
