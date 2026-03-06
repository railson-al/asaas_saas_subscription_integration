from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from datetime import date
from billing.models import Payment
from billing.services import asaas_service

class PaymentView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        value = request.data.get('value')
        billing_type = request.data.get('billing_type')
        description = request.data.get('description', 'One-off payment')
        cpf_cnpj = request.data.get('cpf_cnpj')
        
        if not all([value, billing_type, cpf_cnpj]):
            return Response({"error": "value, billing_type, and cpf_cnpj are required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            customer_id = asaas_service.create_customer(user, cpf_cnpj=cpf_cnpj)
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
