# Extracted API Data

## Metadata

- Title: "Payments API"
- Version: "1.0.0"
- Description: "Tests multiple security scheme types, a global requirement, and a per-endpoint override."
- Contact: API Support (support@example.com)
- License: Apache 2.0 — https://www.apache.org/licenses/LICENSE-2.0.html
- Servers:
  - (none)
- Tags:
  - (none)

## Security

- Global requirements:
  - bearerAuth
- Schemes:
  - **apiKeyAuth**
    - Type: apiKey
    - Location: header
    - Parameter name: X-API-Key
  - **bearerAuth**
    - Type: http
    - Scheme: bearer
    - Bearer format: JWT
  - **oauth2**
    - Type: oauth2
    - Flow: implicit (scopes: payments:read, payments:write)

## Endpoints

### GET /payments
- operationId: "listPayments"
- summary: null
- description: null
- tags: []
- Security: Inherits global security
- Parameters:
  - (none)
- Request body:
  - (none)
- Responses:
  - **200**: All payments
    - application/json: array of `Payment`

### POST /payments
- operationId: "createPayment"
- summary: null
- description: null
- tags: []
- Security:
  - oauth2 (scopes: payments:write)
- Parameters:
  - (none)
- Request body:
  - required
    - application/json: `PaymentInput`
- Responses:
  - **201**: Payment created
    - application/json: `Payment`

### GET /health
- operationId: "healthCheck"
- summary: null
- description: null
- tags: []
- Security: No authentication required
- Parameters:
  - (none)
- Request body:
  - (none)
- Responses:
  - **200**: Service is healthy

## Schemas

### Payment
- Type: object
- Properties:
  - **id**: string *(required)*
  - **amountCents**: integer *(required)*
    - Constraints: minimum=0
  - **currency**: string *(required)*
    - Enum: "USD", "EUR", "GBP"

### PaymentInput
- Type: object
- Properties:
  - **amountCents**: integer *(required)*
    - Constraints: minimum=0
  - **currency**: string *(required)*
    - Enum: "USD", "EUR", "GBP"

## User Stories

As an authenticated user, I want to list my payments.
As an authenticated app (via OAuth2), I want to create a payment on a user's behalf.
As an operator, I want to check service health without authenticating.


## Warnings

- none

## Broken $ref Summary

- Total broken $ref occurrences: 0
- Affected endpoints: 0