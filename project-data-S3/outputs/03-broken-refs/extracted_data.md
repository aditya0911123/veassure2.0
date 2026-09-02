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
    - application/json: ⚠️ unresolvable $ref → #/components/schemas/Invoice

## Schemas

### Order
- Type: object
- Properties:
  - **id**: string *(required)*
  - **customer**: `Customer`
  - **shippingLabel**: ⚠️ unresolvable $ref → #/components/schemas/ShippingLabel

### Customer
- Type: object
- Properties:
  - **name**: string
  - **email**: string

### Invoice
- ⚠️ unresolvable $ref → #/components/schemas/Invoice

### ShippingLabel
- ⚠️ unresolvable $ref → #/components/schemas/ShippingLabel

## User Stories

As a customer, I want to view my past orders.
As a customer, I want to download an invoice for an order.


## Warnings

- Unresolvable $ref: $.paths./orders/{orderId}/invoice.get.responses.200.content.application/json.schema -> #/components/schemas/Invoice
- Unresolvable $ref: $.components.schemas.Order.properties.shippingLabel -> #/components/schemas/ShippingLabel

## Broken $ref Summary

- Total broken $ref occurrences: 2
- Affected endpoints: 2
  - GET /orders
  - GET /orders/{orderId}/invoice