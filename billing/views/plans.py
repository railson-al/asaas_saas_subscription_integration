from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from billing.models import Plan
from billing.serializers import PlanSerializer

class PlanViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing plan instances.
    Provides `list`, `create`, `retrieve`, `update` and `destroy` actions.
    """
    serializer_class = PlanSerializer
    queryset = Plan.objects.all().order_by('monthly_price')
    # Use IsAuthenticatedOrReadOnly to allow public GET requests (listing plans for signup)
    # but require authentication to POST/PUT/DELETE plans. You might want an IsAdminUser permission instead for mutations.
    permission_classes = [IsAuthenticatedOrReadOnly]

