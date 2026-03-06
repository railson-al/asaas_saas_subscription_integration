# Frontend Implementation Guide: Billing & Subscriptions

This guide demonstrates how your frontend (React, Vue, etc.) should interact with the Django billing API when users purchase subscriptions or make one-off payments.

## Prerequisites

All endpoints expect an `Authorization: Bearer <token>` header, since the users must be authenticated to subscribe or pay.

---

## 1. Subscribing to a Plan (Credit Card)

When the user selects a plan and inputs their credit card details in your frontend:

### Step 1: Subscribe

The frontend calls the Django API to create the subscription. Asaas will charge the credit card registered to the customer in Asaas (Note: For this to work out-of-the-box, you should either integrate Asaas' transparent checkout javascript to tokenize the card, or pass the credit card token details to the backend. *Our current backend assumes the customer already has a billing method, or Asaas handles the charge via email. If you need transparent checkout, the backend needs to accept the `creditCardToken` in this payload.*)

**Frontend Request:**

```bash
curl -X POST http://localhost:8000/api/billing/subscribe/ \
-H "Authorization: Bearer <your_access_token>" \
-H "Content-Type: application/json" \
-d '{
    "plan_id": "c92f1b8a-...",
    "billing_type": "CREDIT_CARD",
    "cycle": "MONTHLY"
}'
```

**Response:**

```json
{
    "message": "Subscription created successfully",
    "subscription_id": "ab12...",
    "asaas_subscription_id": "sub_12345"
}
```

### Step 2: Confirmation

The frontend can now show a "Success! Your subscription is active" screen.

---

## 2. Subscribing to a Plan (Pix)

Pix subscriptions require the user to scan a QR code to activate the first month.

### Step 1: Subscribe

The frontend sends the subscription request for `PIX`.

**Frontend Request:**

```bash
curl -X POST http://localhost:8000/api/billing/subscribe/ \
-H "Authorization: Bearer <your_access_token>" \
-H "Content-Type: application/json" \
-d '{
    "plan_id": "c92f1b8a-...",
    "billing_type": "PIX",
    "cycle": "MONTHLY"
}'
```

**Response:**

```json
{
    "message": "Subscription created successfully",
    "subscription_id": "ab12...",
    "asaas_subscription_id": "sub_12345",
    "pix": {
        "encodedImage": "data:image/png;base64,...",
        "payload": "00020101021226...",
        "expirationDate": "2026-03-06 23:59:59"
    }
}
```

### Step 2: Display QR Code

Parse the `pix` object from the response and display the `encodedImage` in an `<img>` tag:

```html
<!-- Example React/Vue -->
<img src={response.pix.encodedImage} alt="Pix QR Code" />
<p>Copy Paste Code: {response.pix.payload}</p>
```

### Step 3: Poll or Listen for Payment (Optional but Recommended)

The user will pay on their phone. Once they pay, Asaas sends a webhook to your Django backend, which updates the local DB.
Your frontend can optionally poll an endpoint (e.g., `/me/`) every 5 seconds to see when `user.subscription.status` changes from `"PENDING"` to `"ACTIVE"`. Once it does, redirect them to the success page!

---

## 3. One-off Payments (Pix)

If you are selling a single product or consulting session.

**Frontend Request:**

```bash
curl -X POST http://localhost:8000/api/billing/pay/ \
-H "Authorization: Bearer <your_access_token>" \
-H "Content-Type: application/json" \
-d '{
    "value": "150.00",
    "billing_type": "PIX",
    "description": "One-hour Consulting"
}'
```

**Response:**

```json
{
    "payment_id": "xy98...",
    "asaas_payment_id": "pay_987654",
    "pix": {
        "encodedImage": "data:image/png;base64,...",
        "payload": "00020101021226..."
    }
}
```

*Display the QR Code exactly as shown in the Subscription Pix example.*

---

## 4. Handling Access Denied (Feature Limits)

When a user tries to access a feature they haven't paid for, the backend will return a `403 Forbidden` error.

**Frontend Example:**

```javascript
async function createCampaign() {
  const response = await fetch('/api/campaigns/', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });

  if (response.status === 403) {
    // The user doesn't have an active subscription, or reached their plan limit.
    // Show a modal: "Upgrade to Pro to create more campaigns!"
    showUpgradeModal();
  }
}
```
