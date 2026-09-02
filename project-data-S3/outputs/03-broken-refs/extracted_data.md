# Extracted API Data

## Metadata

- Title: "Order API"
- Version: "1.0.0"
- Description: "Tests broken/unresolvable $refs at both endpoint level and nested inside a schema."
- Contact: null
- License: null
- Servers: []
- Tags: []

## Security

- Global requirements: []
- Schemes:
  - none

## Endpoints

### GET /orders
- operationId: "listOrders"
- summary: null
- description: null
- tags: []
- security: null
- parameters: []
- request_body: null
- responses: {"200": {"description": "All orders", "content": {"application/json": {"schema": {"type": "array", "items": "Order"}}}}}

### GET /orders/{orderId}/invoice
- operationId: "getOrderInvoice"
- summary: null
- description: null
- tags: []
- security: null
- parameters: [{"name": "orderId", "in": "path", "required": true, "schema": {"type": "string"}}]
- request_body: null
- responses: {"200": {"description": "Invoice document", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Invoice"}}}}}

## Schemas

### Order
```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "string"
    },
    "customer": "Customer",
    "shippingLabel": {
      "$ref": "#/components/schemas/ShippingLabel"
    }
  },
  "required": [
    "id"
  ]
}
```

### Customer
```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string"
    },
    "email": {
      "type": "string"
    }
  }
}
```

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