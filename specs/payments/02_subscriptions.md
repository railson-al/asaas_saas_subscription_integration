# 02. Subscriptions Specification

## Objective

Implement monthly and yearly recurring billing cycles via Asaas Subscriptions to provide automated access to SaaS plans.

## Asaas Endpoints Used

- `POST /v3/subscriptions`: Create a new subscription.
- `PUT /v3/subscriptions/{id}`: Update an existing subscription.
- `DELETE /v3/subscriptions/{id}`: Cancel a subscription.

## Requirements

1. **Create Subscription Payload**:
    - `customer`: Asaas Customer ID
    - `billingType`: `"PIX"` or `"CREDIT_CARD"`
    - `nextDueDate`: Start date of the cycle
    - `value`: Cost of the plan
    - `cycle`: `"MONTHLY"` or `"YEARLY"`
    - `creditCard` / `creditCardHolderInfo` (if `CREDIT_CARD`)

2. **Database Models Needed**:
    - `SaaSPlan`:
        - `id` (UUID)
        - `name` (String)
        - `monthly_price` (Decimal)
        - `yearly_price` (Decimal)
        - `features` (JSON / M2M)
    - `UserSubscription`:
        - `id` (UUID)
        - `user` (FK)
        - `plan` (FK)
        - `asaas_subscription_id` (String)
        - `status` (Choices: ACTIVE, EXPIRED, CANCELED, PAST_DUE)
        - `billing_type` (Choices: PIX, CREDIT_CARD)
        - `cycle` (Choices: MONTHLY, YEARLY)
        - `next_due_date` (Date)

3. **Upgrades / Downgrades flow**:
    - Determine credit left on the current plan.
    - Cancel old Asaas subscription.
    - Create a new Asaas subscription with the pro-rated value and new cycle.
    - Update the local `UserSubscription`.

4. **Status Sync**:
    - Initial creation sets the status based on `billingType` and instant payment feedback.
    - Pix subscriptions will start strictly `PENDING` until the first payment is cleared via Webhook.
