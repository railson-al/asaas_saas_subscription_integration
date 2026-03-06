from django.core.management.base import BaseCommand
from billing.models import Subscription
from billing.services import asaas_service
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Syncs local subscriptions with Asaas API to catch missed webhooks'

    def handle(self, *args, **options):
        # Fetch subscriptions that are PENDING or ACTIVE to ensure they match Asaas
        subs = Subscription.objects.filter(status__in=['PENDING', 'ACTIVE']).exclude(asaas_subscription_id__isnull=True)
        count = 0
        for sub in subs:
            try:
                remote_sub = asaas_service.get_subscription(sub.asaas_subscription_id)
                remote_status = remote_sub.get('status')
                
                # Update status
                changed = False
                if remote_status and sub.status != remote_status:
                    sub.status = remote_status
                    changed = True
                
                # Update next due date if available
                next_due_date = remote_sub.get('nextDueDate')
                if next_due_date and str(sub.next_due_date) != next_due_date:
                    sub.next_due_date = next_due_date
                    changed = True
                    
                if changed:
                    sub.save()
                    count += 1
            except Exception as e:
                logger.error(f"Failed to sync subscription {sub.asaas_subscription_id}: {e}")
                
        self.stdout.write(self.style.SUCCESS(f'Successfully synced {count} subscriptions.'))
