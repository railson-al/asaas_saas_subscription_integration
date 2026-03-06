# 04. Background Tasks Specification

## Objective

Ensure local database state is synchronized with Asaas accurately, catching any edge cases missed by webhooks, and automatically managing subscription statuses.

## Requirements

1. **Daily Sync Task**:
    - Runs once every 24 hours.
    - Queries Asaas for Subscriptions or Payments that should have been updated but weren't (e.g., missed webhooks).
    - Syncs `next_due_date` and `status` with the local `UserSubscription`.

2. **Access Revocation Task (Grace Period Checker)**:
    - Runs periodically (e.g., every hour or daily).
    - Checks `UserSubscription` records where `status = ACTIVE` AND `next_due_date < (Today - GracePeriod)`.
    - If found, changes the status to `PAST_DUE` or `CANCELED` (if configured), immediately restricting user access as defined in the Permissions spec.

3. **Pending Pix Expiration Task**:
    - Runs periodically.
    - Checks pending Pix payments. If the Pix QR code has expired and no payment was received, mark local `Payment` as `CANCELED`.

## Tech Stack

- The background task processor will be configured according to the project's standards (e.g., Celery with Redis/RabbitMQ, or Huey, or Django Q).
- Tasks should be idempotent and handle potential network failures to Asaas gracefully.
