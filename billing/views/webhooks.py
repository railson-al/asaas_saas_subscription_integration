from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.conf import settings
from billing.models import Subscription, Payment
import logging

logger = logging.getLogger(__name__)

class WebhookView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        token = request.headers.get('asaas-access-token')
        if not token or token != settings.ASAAS_WEBHOOK_TOKEN:
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
            
        event = request.data.get('event')
        payment_data = request.data.get('payment', {})
        subscription_id = payment_data.get('subscription')
        payment_id = payment_data.get('id')
        
        try:
            if event == 'PAYMENT_RECEIVED':
                if payment_id:
                    Payment.objects.filter(asaas_payment_id=payment_id).update(status='RECEIVED')
                if subscription_id:
                    sub = Subscription.objects.filter(asaas_subscription_id=subscription_id).first()
                    if sub:
                        sub.status = 'ACTIVE'
                        sub.save()
                        
            elif event == 'PAYMENT_OVERDUE':
                if payment_id:
                    Payment.objects.filter(asaas_payment_id=payment_id).update(status='OVERDUE')
                    
            elif event == 'PAYMENT_REFUNDED':
                if payment_id:
                    Payment.objects.filter(asaas_payment_id=payment_id).update(status='REFUNDED')
                    
            elif event == 'SUBSCRIPTION_CANCELED':
                sub_id = request.data.get('subscription', {}).get('id')
                if sub_id:
                    Subscription.objects.filter(asaas_subscription_id=sub_id).update(status='CANCELED')

        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            
        return Response({"status": "received"}, status=status.HTTP_200_OK)
