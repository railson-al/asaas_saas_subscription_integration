from django.urls import path, include
from rest_framework.routers import DefaultRouter
from billing.views import SubscribeView, PaymentView, WebhookView, PlanViewSet, SubscriptionStatusView

router = DefaultRouter()
router.register(r'plans', PlanViewSet, basename='plan')

urlpatterns = [
    path('', include(router.urls)),
    path('me/', SubscriptionStatusView.as_view(), name='subscription_status'),
    path('subscribe/', SubscribeView.as_view(), name='subscribe'),
    path('pay/', PaymentView.as_view(), name='pay'),
    path('webhooks/asaas/', WebhookView.as_view(), name='webhook_asaas'),
]
