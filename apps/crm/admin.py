from django.contrib import admin
from .models import (Lead, FollowUp, CallLog, Meeting, Feedback, Complaint,
                      Suggestion, LoyaltyTier, LoyaltyAccount, LoyaltyTransaction,
                      Referral, Campaign)

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['get_full_name','phone','source','status','assigned_to']
    list_filter  = ['status','source']
    search_fields= ['first_name','last_name','phone']

admin.site.register(FollowUp)
admin.site.register(CallLog)
admin.site.register(Meeting)
admin.site.register(Feedback)

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ['subject','member','priority','status','created_at']
    list_filter  = ['status','priority']

admin.site.register(Suggestion)
admin.site.register(LoyaltyTier)
admin.site.register(LoyaltyAccount)
admin.site.register(LoyaltyTransaction)
admin.site.register(Referral)
admin.site.register(Campaign)
