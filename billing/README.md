# Billing App (Asaas Integration)

This Django app provides a complete, native integration with the [Asaas Payment Gateway](https://docs.asaas.com/) for a SaaS platform. It handles one-off payments (Pix, Credit Card), recurring subscriptions (Monthly, Yearly), webhook processing, and plan-based feature validation.

## Features

- **Plans & Subscriptions**: Create SaaS plans with JSON-based feature limits and subscribe users to them.
- **Payment Processing**: Natively supports Asaas Pix (with instant QR Code generation) and Credit Card payments.
- **Webhooks**: Real-time synchronization of Asaas events (`PAYMENT_RECEIVED`, `PAYMENT_OVERDUE`, `SUBSCRIPTION_CANCELED`).
- **Permissions**: DRF BasePermission (`HasActiveSubscription`) to strictly protect API endpoints based on active subscriptions.
- **Background Tasks**: Django management commands for synchronizing states, revoking expired access, and checking pending Pix payments.

---

## Configuration

Ensure the following environment variables are set in your `.env` file or environment (they are loaded in `core/settings.py`):

```env
ASAAS_API_URL=https://sandbox.asaas.com/api/v3
ASAAS_API_KEY=your_asaas_api_key_here
ASAAS_WEBHOOK_TOKEN=your_asaas_webhook_token_here
```

---

## Core Models

1. **`Plan`**: Defines a SaaS tier with a name, monthly/yearly prices, and a `features` JSON object.

    ```python
    features = {"max_projects": 5, "premium_support": True}
    ```

2. **`Subscription`**: Links a `User` to a `Plan`. Tracks the Asaas subscription ID, billing cycle, due dates, and real-time status (`ACTIVE`, `PENDING`, `PAST_DUE`, `CANCELED`).
3. **`Payment`**: Tracks individual charges (for subscriptions or one-off purchases).

---

## API Endpoints & Integration Examples

### 1. Create a Subscription (`POST /api/billing/subscribe/`)

Used to subscribe a user to a specific plan.

**Request (cURL):**

```bash
curl -X POST http://localhost:8000/api/billing/subscribe/ \
-H "Authorization: Bearer <your_jwt_token>" \
-H "Content-Type: application/json" \
-d '{
    "plan_id": "<uuid-of-the-plan>",
    "billing_type": "PIX",
    "cycle": "MONTHLY"
}'
```

**Response (201 Created):**

```json
{
    "message": "Subscription created successfully",
    "subscription_id": "local-uuid",
    "asaas_subscription_id": "sub_123456789"
}
```

### 2. Create a One-off Payment (`POST /api/billing/pay/`)

Used for single charges. If `PIX` is selected, the response includes the Pix QR code payload to display to the user.

**Request (cURL):**

```bash
curl -X POST http://localhost:8000/api/billing/pay/ \
-H "Authorization: Bearer <your_jwt_token>" \
-H "Content-Type: application/json" \
-d '{
    "value": "150.00",
    "billing_type": "PIX",
    "description": "Consulting Session"
}'
```

**Response (201 Created):**

```json
{
    "payment_id": "local-uuid",
    "asaas_payment_id": "pay_987654321",
    "pix": {
        "encodedImage": "data:image/png;base64,...",
        "payload": "00020101021226...",
        "expirationDate": "2026-03-06 23:59:59"
    }
}
```

### 3. Asaas Webhooks (`POST /api/billing/webhooks/asaas/`)

This endpoint is responsible for keeping the local database in sync with Asaas.
**Setup in Asaas:**

- URL: `https://yourdomain.com/api/billing/webhooks/asaas/`
- Events to listen to: Payments, Subscriptions

---

## Validating Features in the App

To protect a view relying on an active subscription:

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from billing.permissions import HasActiveSubscription, check_feature_limit

class CreateProjectView(APIView):
    permission_classes = [HasActiveSubscription] # Must have an active subscription

    def post(self, request):
        user = request.user
        current_projects = user.projects.count()
        
        # Check if the user plan allows another project
        if not check_feature_limit(user, 'max_projects', current_projects):
            return Response({"error": "Plan limit reached."}, status=403)
            
        # Create project...
        return Response({"status": "Created"})
```

---

## Background Tasks (Cron Jobs)

You must configure `cron` (or a task runner like Celery) to run these Django management commands periodically to maintain standard state matching:

1. **Daily Sync (Runs at 00:00)**: Catches any missed webhooks and updates local Subscriptions to securely match Asaas.

   ```bash
   python manage.py sync_asaas_subscriptions
   ```

2. **Revoke Expired Access (Runs Daily/Hourly)**: Overrides Active status moving it to Past Due if out of grace period.

   ```bash
   python manage.py revoke_expired_access --grace-period 3
   ```

3. **Check Pix Expiration (Runs Hourly)**: Clears pending Pix payments that users abandoned.

   ```bash
   python manage.py check_expired_pix
   ```
