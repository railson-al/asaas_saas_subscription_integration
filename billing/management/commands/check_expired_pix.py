from django.core.management.base import BaseCommand
from billing.models import Payment
from billing.services import asaas_service
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Checks pending Pix payments with Asaas and cancels them locally if expired'

    def handle(self, *args, **options):
        payments = Payment.objects.filter(
            billing_type='PIX', 
            status='PENDING', 
            asaas_payment_id__isnull=False
        )
        
        count = 0
        for payment in payments:
            try:
                # Optionally check if due_date is deeply past expiration. 
                # Better: directly check Asaas status
                remote_pay = asaas_service.get_payment(payment.asaas_payment_id)
                remote_status = remote_pay.get('status')
                
                if remote_status in ['EXPIRED', 'OVERDUE', 'CANCELED']:
                    payment.status = 'CANCELED' 
                    payment.save()
                    count += 1
                elif remote_status == 'RECEIVED':
                    payment.status = 'RECEIVED'
                    payment.save()
                    count += 1
            except Exception as e:
                logger.error(f"Failed to check Pix payment {payment.asaas_payment_id}: {e}")
                
        self.stdout.write(self.style.SUCCESS(f'Processed {count} pending Pix payments.'))
