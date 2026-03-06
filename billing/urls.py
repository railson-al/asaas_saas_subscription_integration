from django.urls import path
from .views import SubscribeView, PaymentView, WebhookView

urlpatterns = [
    path('subscribe/', SubscribeView.as_view(), name='subscribe'),
    path('pay/', PaymentView.as_view(), name='pay'),
    path('webhooks/asaas/', WebhookView.as_view(), name='webhook_asaas'),
]
