from django.contrib import admin
from .models import SupportTicket, TicketReply, FreezeRequest, RenewalRequest

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ['subject','member','category','status','created_at']
    list_filter  = ['status','category']

admin.site.register(TicketReply)
admin.site.register(FreezeRequest)
admin.site.register(RenewalRequest)
