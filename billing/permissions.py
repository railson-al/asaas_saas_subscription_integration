from rest_framework import permissions

class HasActiveSubscription(permissions.BasePermission):
    """
    Allows access only to users with an ACTIVE subscription.
    """
    message = "You must have an active subscription to perform this action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if the user has a subscription and it's ACTIVE
        try:
            return request.user.subscription.status == 'ACTIVE'
        except Exception:
            # If request.user.subscription raises configured RelatedObjectDoesNotExist
            return False

def check_feature_limit(user, feature_key, current_count):
    """
    Utility function to check if the user has reached a specific feature limit.
    """
    try:
        plan = user.subscription.plan
        features = plan.features or {}
        limit = features.get(feature_key, 0)
        
        if limit == -1: # -1 could mean unlimited
            return True
            
        return current_count < limit
    except Exception:
        return False
