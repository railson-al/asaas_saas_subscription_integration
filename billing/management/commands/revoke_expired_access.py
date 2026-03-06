from django.core.management.base import BaseCommand
from billing.models import Subscription
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Revokes access for active subscriptions that are past their grace period'

    def add_arguments(self, parser):
        parser.add_argument(
            '--grace-period',
            type=int,
            default=3,
            help='Grace period in days (default: 3)'
        )

    def handle(self, *args, **options):
        grace_period_days = options['grace_period']
        cutoff_date = timezone.now().date() - timedelta(days=grace_period_days)
        
        expired_subs = Subscription.objects.filter(
            status='ACTIVE',
            next_due_date__lt=cutoff_date
        )
        
        count = expired_subs.update(status='PAST_DUE')
        
        self.stdout.write(self.style.SUCCESS(f'Revoked access for {count} expired subscriptions.'))
