# 01. Payment Methods Specification

## Objective

Implement Pix and Credit Card payment options using Asaas API to handle one-off charges or initial subscription payments.

## Asaas Endpoints Used

- `POST /v3/payments`: Create a new payment.
- `GET /v3/payments/{id}/pixQrCode`: Get Pix QR Code after payment creation.

## Requirements

1. **Payload Structure for Pix**:
    - `customer`: Asaas Customer ID
    - `billingType`: `"PIX"`
    - `value`: Payment amount
    - `dueDate`: Date the payment is due
    - *Expected Flow*: The system creates the payment, fetches the Pix QR code payload using the `id`, and returns it to the frontend for the user to scan.

2. **Payload Structure for Credit Card**:
    - `customer`: Asaas Customer ID
    - `billingType`: `"CREDIT_CARD"`
    - `value`: Payment amount
    - `dueDate`: Date the payment is due
    - `creditCard`: Object containing `holderName`, `number`, `expiryMonth`, `expiryYear`, `ccv`.
    - `creditCardHolderInfo`: Object containing `name`, `email`, `cpfCnpj`, `postalCode`, `addressNumber`, `addressComplement`, `phone`, `mobilePhone`.
    - *Expected Flow*: The system creates the payment and immediately attempts to process the credit card charge. Returns success or failure based on the response.

3. **Database Models Needed**:
    - `Payment`:
        - `id` (UUID)
        - `user` (FK)
        - `asaas_payment_id` (String)
        - `value` (Decimal)
        - `billing_type` (Choices: PIX, CREDIT_CARD)
        - `status` (Choices: PENDING, RECEIVED, OVERDUE, etc.)
        - `due_date` (Date)
        - `created_at` (DateTime)
        - `updated_at` (DateTime)

## Error Handling

- Invalid credit card info needs to return standard validation errors.
- External API down/timeouts should throw 503 Service Unavailable and suggest retrying.
