from django.contrib import admin
from .models import Account, JournalEntry, JournalLine, Income, Expense, Budget, TaxRecord

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['code','name','account_type','is_active']
    list_filter  = ['account_type','is_active']


class JournalLineInline(admin.TabularInline):
    model = JournalLine
    extra = 2


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ['entry_number','date','description','status']
    list_filter  = ['status']
    inlines      = [JournalLineInline]


admin.site.register(Income)
admin.site.register(Expense)
admin.site.register(Budget)
admin.site.register(TaxRecord)
