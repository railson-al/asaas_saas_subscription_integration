import uuid
from django.db import models
from django.conf import settings

class Plan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    yearly_price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.name

class Subscription(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACTIVE', 'Active'),
        ('PAST_DUE', 'Past Due'),
        ('CANCELED', 'Canceled'),
        ('EXPIRED', 'Expired'),
    ]
    BILLING_TYPE_CHOICES = [
        ('PIX', 'Pix'),
        ('CREDIT_CARD', 'Credit Card'),
    ]
    CYCLE_CHOICES = [
        ('MONTHLY', 'Monthly'),
        ('YEARLY', 'Yearly'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(Plan, on_delete=models.RESTRICT)
    asaas_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    billing_type = models.CharField(max_length=20, choices=BILLING_TYPE_CHOICES)
    cycle = models.CharField(max_length=20, choices=CYCLE_CHOICES)
    next_due_date = models.DateField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.plan.name} ({self.status})"

class Payment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RECEIVED', 'Received'),
        ('OVERDUE', 'Overdue'),
        ('REFUNDED', 'Refunded'),
        ('CANCELED', 'Canceled')
    ]
    BILLING_TYPE_CHOICES = [
        ('PIX', 'Pix'),
        ('CREDIT_CARD', 'Credit Card'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    asaas_payment_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    billing_type = models.CharField(max_length=20, choices=BILLING_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    due_date = models.DateField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.asaas_payment_id} - {self.status}"
