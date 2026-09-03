# Extracted API Data

## Metadata

- Title: "Order API"
- Version: "1.0.0"
- Description: "Tests broken/unresolvable $refs at both endpoint level and nested inside a schema."
- Contact: (none)
- License: (none)
- Servers:
  - (none)
- Tags:
  - (none)

## Security

- Global requirements:
  - (none)
- Schemes:
  - (none)

## Endpoints

### GET /orders
- operationId: "listOrders"
- summary: null
- description: null
- tags: []
- Security: Inherits global security
- Parameters:
  - (none)
- Request body:
  - (none)
- Responses:
  - **200**: All orders
    - application/json: array of `Order`

### GET /orders/{orderId}/invoice
- operationId: "getOrderInvoice"
- summary: null
- description: null
- tags: []
- Security: Inherits global security
- Parameters:
  - **orderId** (path, required): string
- Request body:
  - (none)
- Responses:
  - **200**: Invoice document
    - application/json: object

## Schemas

### Order
- Type: object
- Properties:
  - **id**: string *(required)*
  - **customer**: `Customer`
  - **shippingLabel**: object

### Customer
- Type: object
- Properties:
  - **name**: string
  - **email**: string

## User Stories

As a customer, I want to view my past orders.
As a customer, I want to download an invoice for an order.

