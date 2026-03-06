# 05. Webhooks Specification

## Objective

Process incoming event webhooks from Asaas to update the local database in real-time, handling payments, subscriptions, and customer data changes securely.

## Asaas Settings

- Configure standard webhook in the Asaas dashboard to point to `POST /api/webhooks/asaas/`.
- Ensure a secure token is passed in headers to validate requests originating from Asaas.

## Requirements

1. **Endpoint**: `POST /api/webhooks/asaas/`
    - Returns `200 OK` immediately upon passing basic validation and saving the raw payload to process asynchronously if possible.

2. **Security validation**:
    - Check the provided headers (`asaas-access-token` for Asaas API V3 standard webhook config).
    - Reject unauthorized requests.

3. **Events to Handle**:
    - **Payments**:
        - `PAYMENT_RECEIVED`: Update local `Payment` status to `RECEIVED`. If it's the first payment for a pending subscription, activate the `UserSubscription`.
        - `PAYMENT_OVERDUE`: Mark local `Payment` as `OVERDUE`.
        - `PAYMENT_REFUNDED`: Mark as `REFUNDED` and potentially downgrade subscription.
    - **Subscriptions**:
        - `SUBSCRIPTION_CANCELED`: If the user cancels or Asaas cancels due to repeated payment failures, mark local `UserSubscription` as `CANCELED`.
    - **Customers**:
        - `CUSTOMER_UPDATED`: Sync any changes manually made in the Asaas portal back to the local `User` or `Profile` record to keep them consistent.

4. **Idempotency**:
    - Webhook processing must ensure identical payloads (e.g. delivered twice) do not create duplicate records or perform duplicate actions (like double crediting an account).
    - Easiest way: check if `status` is already updated before saving.
