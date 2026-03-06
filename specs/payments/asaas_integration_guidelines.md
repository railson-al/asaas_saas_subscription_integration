# Asaas Payment Integration Guidelines

## Overview

This document outlines the specifications and guidelines for integrating Asaas into the SaaS platform to handle payments, subscriptions, and webhooks.

## 1. Supported Payment Methods

The platform will support two distinct billing types natively handled by Asaas:

- **Pix** (`billingType: PIX`): Instant payments with dynamic QR codes.
- **Credit Card** (`billingType: CREDIT_CARD`): Secure, direct credit card charges.

When creating a payment (`POST /v3/payments`) or a subscription (`POST /v3/subscriptions`), the `billingType` parameter must be explicitly passed.

## 2. Subscription Plans (Monthly & Yearly)

The application will offer recurring billing via Asaas Subscriptions (`POST /v3/subscriptions`).

- **Cycles**: Subscriptions should be created with `cycle: MONTHLY` or `cycle: YEARLY` depending on the user's selected plan.
- **Upgrades/Downgrades**: Managed by updating the existing subscription (`PUT /v3/subscriptions/{id}`) or canceling and creating a new one, prorating if necessary.

## 3. Plan-based Permissions and Feature Validation

Access control should be tied to the active subscription plan:

- **Local State**: The app must mirror the user's plan and payment status locally in the database.
- **Features & Limits**: Permissions to access specific features (e.g., maximum campaigns, SLAs) must be validated against the active plan stored locally before fulfilling user requests.
- **Grace Periods**: Implement a grace period for overdue payments before revoking access.

## 4. Background Tasks & Monitoring

To ensure the local state is consistent with Asaas:

- **Daily Sync Task**: A scheduled background job (e.g., using Celery or Huey) should run daily to check for overdue subscriptions or edge-case sync failures.
- **Access Revocation Task**: A task should automatically downgrade or block users when their subscription status turns `OVERDUE` beyond the allowed grace period, or if the subscription gets `CANCELED`.

## 5. Webhook Processing

The app must expose an endpoint to process Asaas Webhooks to keep the state synchronized in real-time.

- **Payment Events**: Listen for `PAYMENT_RECEIVED`, `PAYMENT_OVERDUE`, `PAYMENT_REFUNDED`, etc. Updates the local payment records.
- **Subscription Events**: Listen for changes in subscription statuses to activate or deactivate plan features immediately.
- **Customer Events**: Listen for customer information updates to keep local records synced if changed directly via Asaas.
- **Idempotency**: Webhook processing must be idempotent to handle duplicate event deliveries securely. Provide immediate `200 OK` response to Asaas and process the payload asynchronously via background tasks.
