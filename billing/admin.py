from django.contrib import admin
from .models import Plan, Subscription, Payment

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'monthly_price', 'yearly_price')

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'billing_type', 'cycle', 'next_due_date')
    list_filter = ('status', 'billing_type', 'cycle')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'asaas_payment_id', 'value', 'status', 'due_date')
    list_filter = ('status', 'billing_type')
