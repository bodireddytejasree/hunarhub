from django.contrib import admin

from . import models

admin.site.register(models.Category)
admin.site.register(models.Service)
admin.site.register(models.Product)
admin.site.register(models.Review)


@admin.register(models.EntrepreneurProfile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'category', 'location', 'is_verified', 'is_available')
    list_filter = ('is_verified', 'category')
    search_fields = ('business_name', 'location', 'user__username')
    actions = ['approve']

    @admin.action(description='Approve selected entrepreneurs')
    def approve(self, request, queryset):
        queryset.update(is_verified=True)


@admin.register(models.ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('service', 'customer', 'status', 'created_at')
    list_filter = ('status',)


@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('product', 'customer', 'quantity', 'total_price', 'status', 'created_at')
    list_filter = ('status',)


@admin.register(models.Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('subject', 'entrepreneur', 'customer', 'status', 'created_at')
    list_filter = ('status',)
