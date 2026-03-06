from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.conf import settings
from .models import Plan, Subscription, Payment
from .services import asaas_service
from datetime import date
import logging

logger = logging.getLogger(__name__)

class SubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        plan_id = request.data.get('plan_id')
        billing_type = request.data.get('billing_type') # PIX or CREDIT_CARD
        cycle = request.data.get('cycle') # MONTHLY or YEARLY
        
        if not all([plan_id, billing_type, cycle]):
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)
            
        plan = get_object_or_404(Plan, id=plan_id)
        
        try:
            customer_id = asaas_service.create_customer(user)
            value = plan.monthly_price if cycle == 'MONTHLY' else plan.yearly_price
            next_due_date = date.today()
            
            asaas_sub = asaas_service.create_subscription(
                customer_id=customer_id,
                billing_type=billing_type,
                value=value,
                cycle=cycle,
                next_due_date=next_due_date,
                description=f"Subscription to {plan.name} ({cycle})"
            )
            
            Subscription.objects.filter(user=user).delete()
            
            sub = Subscription.objects.create(
                user=user,
                plan=plan,
                asaas_subscription_id=asaas_sub.get('id'),
                status='PENDING',
                billing_type=billing_type,
                cycle=cycle,
                next_due_date=next_due_date
            )
            
            response_data = {
                "message": "Subscription created successfully",
                "subscription_id": sub.id,
                "asaas_subscription_id": asaas_sub.get('id')
            }

            if billing_type == 'PIX':
                # Fetch the charges associated with this subscription
                payments_data = asaas_service.get_subscription_payments(asaas_sub.get('id'))
                # Asaas returns a paginated list of payments in the 'data' field
                payments = payments_data.get('data', [])
                if payments:
                    # The most recent payment (first installment)
                    first_payment = payments[0]
                    first_payment_id = first_payment.get('id')
                    
                    # Create a local Payment record for this installment too
                    Payment.objects.create(
                        user=user,
                        asaas_payment_id=first_payment_id,
                        value=value,
                        billing_type='PIX',
                        status='PENDING',
                        due_date=next_due_date
                    )
                    
                    # Get and include Pix QR Code
                    pix_data = asaas_service.get_pix_qrcode(first_payment_id)
                    response_data['pix'] = pix_data
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except asaas_service.AsaasAPIException as e:
            return Response({"error": str(e)}, status=e.status_code)

class PaymentView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        value = request.data.get('value')
        billing_type = request.data.get('billing_type')
        description = request.data.get('description', 'One-off payment')
        
        if not all([value, billing_type]):
            return Response({"error": "value and billing_type are required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            customer_id = asaas_service.create_customer(user)
            due_date = date.today()
            
            asaas_pay = asaas_service.create_payment(
                customer_id=customer_id,
                billing_type=billing_type,
                value=value,
                due_date=due_date,
                description=description
            )
            
            payment = Payment.objects.create(
                user=user,
                asaas_payment_id=asaas_pay.get('id'),
                value=value,
                billing_type=billing_type,
                status='PENDING',
                due_date=due_date
            )
            
            response_data = {
                "payment_id": payment.id,
                "asaas_payment_id": payment.asaas_payment_id,
            }
            
            if billing_type == 'PIX' and payment.asaas_payment_id:
                pix_data = asaas_service.get_pix_qrcode(payment.asaas_payment_id)
                response_data['pix'] = pix_data
                
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except asaas_service.AsaasAPIException as e:
            return Response({"error": str(e)}, status=e.status_code)

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
