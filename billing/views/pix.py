from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from billing.models import Payment
from billing.services import asaas_service


class PendingPixView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payment = (
            Payment.objects.filter(user=request.user, billing_type='PIX', status='PENDING')
            .order_by('-due_date')
            .first()
        )
        if not payment:
            return Response({"detail": "No pending PIX payment"}, status=status.HTTP_404_NOT_FOUND)

        try:
            pix_data = asaas_service.get_pix_qrcode(payment.asaas_payment_id)
        except asaas_service.AsaasAPIException as e:
            return Response({"detail": str(e)}, status=e.status_code)

        return Response({
            "payment_id": str(payment.id),
            "asaas_payment_id": payment.asaas_payment_id,
            "value": str(payment.value),
            "due_date": payment.due_date,
            "encodedImage": pix_data.get("encodedImage"),
            "payload": pix_data.get("payload"),
            "expirationDate": pix_data.get("expirationDate"),
        })
