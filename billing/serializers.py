from rest_framework import serializers
from .models import Plan, Subscription, Payment

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ['id', 'name', 'monthly_price', 'yearly_price', 'features']

class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    
    class Meta:
        model = Subscription
        fields = ['id', 'status', 'billing_type', 'cycle', 'next_due_date', 'plan']

