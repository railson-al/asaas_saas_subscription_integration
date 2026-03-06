# 03. Plan-based Permissions and Feature Validation

## Objective

Implement fine-grained access control so users can only access endpoints and features corresponding to their active `SaaSPlan`.

## Requirements

1. **Plan Feature Definition**:
    - Use a JSONB field (`JSONField` in Django, assuming PostgreSQL is used) on the `SaaSPlan` model to store feature limits and booleans.
    - JSONB provides high performance, flexibility to add new features without schema migrations, and allows efficient querying.
    - Ex: `features = {"max_projects": 3, "can_export_pdf": false}` vs `features = {"max_projects": -1, "can_export_pdf": true}`.

2. **Validation Layer**:
    - **Middleware or Base View Permission**:
        - Create a custom DRF `BasePermission` or view decorator (e.g., `HasActiveSubscription`, `HasFeatureX`).
        - The permission checks if `request.user.subscription.status == 'ACTIVE'`.
    - **Usage Limits**:
        - Before creating a new resource (e.g., a Project), check `current_project_count < limit`.

3. **Grace Period**:
    - Define a grace period policy (e.g., 3 days after `next_due_date`).
    - Status transitions from `ACTIVE` to `PAST_DUE`.
    - While `PAST_DUE`, the user might still have read-only access or limited access, but no new write actions, based on business rules.
    - Endpoints should return `402 Payment Required` with an actionable message prompting payment.

4. **Integration details**:
    - `UserSubscription` model holds a cached status.
    - Permissions class exclusively checks this local status to avoid making synchronous requests to Asaas during normal operation.
