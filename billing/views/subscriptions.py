from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from datetime import date
from billing.models import Plan, Subscription, Payment
from billing.services import asaas_service
from billing.serializers import SubscriptionSerializer

class SubscriptionStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        subscription = getattr(request.user, 'subscription', None)
        if not subscription:
            return Response({"status": "no_subscription"}, status=status.HTTP_200_OK)
            
        serializer = SubscriptionSerializer(subscription)
        return Response(serializer.data)

class SubscribeView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        plan_id = request.data.get('plan_id')
        billing_type = request.data.get('billing_type') # PIX or CREDIT_CARD
        cycle = request.data.get('cycle') # MONTHLY or YEARLY
        cpf_cnpj = request.data.get('cpf_cnpj')
        
        if not all([plan_id, billing_type, cycle, cpf_cnpj]):
            return Response({"error": "Missing required fields (plan_id, billing_type, cycle, or cpf_cnpj)"}, status=status.HTTP_400_BAD_REQUEST)
            
        plan = get_object_or_404(Plan, id=plan_id)
        
        try:
            customer_id = asaas_service.create_customer(user, cpf_cnpj=cpf_cnpj)
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
                payments_data = asaas_service.get_subscription_payments(asaas_sub.get('id'))
                payments = payments_data.get('data', [])
                if payments:
                    first_payment = payments[0]
                    first_payment_id = first_payment.get('id')
                    
                    Payment.objects.create(
                        user=user,
                        asaas_payment_id=first_payment_id,
                        value=value,
                        billing_type='PIX',
                        status='PENDING',
                        due_date=next_due_date
                    )
                    
                    pix_data = asaas_service.get_pix_qrcode(first_payment_id)
                    response_data['pix'] = pix_data
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except asaas_service.AsaasAPIException as e:
            return Response({"error": str(e)}, status=e.status_code)
