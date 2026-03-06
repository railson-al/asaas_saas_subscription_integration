from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date
from .models import Plan, Subscription, Payment
from .permissions import check_feature_limit
from unittest.mock import patch

class BillingModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.plan = Plan.objects.create(
            name='Pro Plan',
            monthly_price=Decimal('29.90'),
            yearly_price=Decimal('290.00'),
            features={'max_projects': 5}
        )

    def test_plan_str(self):
        self.assertEqual(str(self.plan), 'Pro Plan')

    def test_feature_limit_check(self):
        Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            billing_type='CREDIT_CARD',
            cycle='MONTHLY',
            status='ACTIVE'
        )
        
        self.assertTrue(check_feature_limit(self.user, 'max_projects', 3))
        self.assertFalse(check_feature_limit(self.user, 'max_projects', 5))
        self.assertFalse(check_feature_limit(self.user, 'max_projects', 10))

class BillingWebhookTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser2', password='password')
        self.plan = Plan.objects.create(
            name='Basic Plan',
            monthly_price=Decimal('9.90'),
            yearly_price=Decimal('90.00'),
            features={'max_projects': 1}
        )
        self.subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            asaas_subscription_id='sub_123',
            billing_type='PIX',
            cycle='MONTHLY',
            status='PENDING'
        )
        
    @patch('django.conf.settings.ASAAS_WEBHOOK_TOKEN', 'secret-token')
    def test_webhook_payment_received_activates_subscription(self):
        payload = {
            "event": "PAYMENT_RECEIVED",
            "payment": {
                "id": "pay_123",
                "subscription": "sub_123"
            }
        }
        
        response = self.client.post(
            '/api/billing/webhooks/asaas/',
            data=payload,
            content_type='application/json',
            HTTP_ASAAS_ACCESS_TOKEN='secret-token'
        )
        
        self.assertEqual(response.status_code, 200)
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, 'ACTIVE')
