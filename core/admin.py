from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from .models import *

# Simple registrations (no customization needed)
admin.site.register(Visitor)
admin.site.register(Complaint)
admin.site.register(Facility)
admin.site.register(FacilityBooking)
admin.site.register(Notice)
admin.site.register(EmergencyAlert)

# User — customized
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display  = ['email', 'first_name', 'last_name', 'role', 'is_active']
    list_filter   = ['role']
    search_fields = ['email']

# MaintenancePayment — customized + Create Bills button
@admin.register(MaintenancePayment)
class MaintenancePaymentAdmin(admin.ModelAdmin):
    list_display  = ['resident', 'month', 'amount', 'payment_status', 'payment_date']
    list_filter   = ['payment_status', 'month']
    search_fields = ['resident__email']
    change_list_template = "admin/maintenance_payment_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('create-bills/', self.admin_site.admin_view(self.create_bills_redirect), name='create_bills_redirect'),
        ]
        return custom + urls

    def create_bills_redirect(self, request):
        return redirect('admin_create_bill')