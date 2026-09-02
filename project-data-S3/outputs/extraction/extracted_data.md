# Extracted API Data

## Metadata

- Title: "Pet Store API"
- Version: "2.1.0"
- Description: "A comprehensive pet store API for managing pets, orders, and customers."
- Contact: Pet Store Support (support@petstore.com)
- License: MIT — https://opensource.org/licenses/MIT
- Servers:
  - https://api.petstore.com/v2 — Production server
  - https://staging.petstore.com/v2 — Staging server
- Tags:
  - Pets — Operations for managing pets
  - Orders — Operations for managing orders
  - Customers — Operations for managing customers

## Security

- Global requirements:
  - BearerAuth
- Schemes:
  - **BearerAuth**
    - Type: http
    - Scheme: bearer
    - Bearer format: JWT
    - Description: JWT Bearer token. Include in Authorization header.
  - **ApiKeyAuth**
    - Type: apiKey
    - Location: header
    - Parameter name: X-API-Key
    - Description: API key for admin operations.

## Endpoints

### GET /pets
- operationId: "listPets"
- summary: "List all pets"
- description: "Returns a paginated list of all pets available in the store. Supports filtering by status and species."
- tags: ["Pets"]
- Security: Inherits global security
- Parameters:
  - **status** (query, optional): string
    - Description: Filter pets by availability status
  - **species** (query, optional): string
    - Description: Filter pets by species
  - **limit** (query, optional): integer (int32)
    - Description: Maximum number of pets to return
  - **X-Request-ID** (header, optional): string
    - Description: Optional request tracking ID
- Request body:
  - (none)
- Responses:
  - **200**: Paginated list of pets returned successfully
    - application/json: `PetListResponse`
  - **400**: Invalid query parameters supplied
    - application/json: `ErrorResponse`
  - **401**: Unauthorized - missing or invalid Bearer token
    - application/json: `ErrorResponse`
  - **500**: Internal server error
    - application/json: `ErrorResponse`
- Examples:
  - Response 200 (application/json):
    - **dogExample**: Example with a dog — {"data": [{"id": 1, "name": "Buddy", "species": "dog", "breed": "Labrador", "status": "available", "price": 299.99}], "total": 1, "page": 1}

### POST /pets
- operationId: "createPet"
- summary: "Create a new pet"
- description: "Adds a new pet to the store inventory. Requires ADMIN role."
- tags: ["Pets"]
- Security:
  - BearerAuth
  - ApiKeyAuth
- Parameters:
  - (none)
- Request body:
  - required
    - application/json: `CreatePetRequest`
- Responses:
  - **201**: Pet created successfully
    - application/json: `Pet`
  - **400**: Invalid pet data supplied
    - application/json: `ErrorResponse`
  - **401**: Unauthorized
    - application/json: `ErrorResponse`
  - **403**: Forbidden - insufficient permissions
    - application/json: `ErrorResponse`
- Examples:
  - Request body (application/json):
    - {"name": "Max", "species": "dog", "breed": "Golden Retriever", "age": 2, "price": 499.99, "status": "available", "tags": ["friendly", "trained"]}

### GET /pets/{petId}
- operationId: "getPetById"
- summary: "Get pet by ID"
- description: "Returns a single pet by its unique identifier."
- tags: ["Pets"]
- Security: Inherits global security
- Parameters:
  - **petId** (path, required): integer (int64)
    - Description: Unique identifier of the pet
- Request body:
  - (none)
- Responses:
  - **200**: Pet returned successfully
    - application/json: `Pet`
  - **404**: Pet not found
    - application/json: `ErrorResponse`
  - **500**: Internal server error
    - application/json: `ErrorResponse`

### PUT /pets/{petId}
- operationId: "updatePet"
- summary: "Update a pet"
- description: "Updates all fields of an existing pet. Partial updates not supported \u2014 use PATCH instead."
- tags: ["Pets"]
- Security: Inherits global security
- Parameters:
  - **petId** (path, required): integer (int64)
    - Description: Unique identifier of the pet to update
- Request body:
  - required
    - application/json: `UpdatePetRequest`
- Responses:
  - **200**: Pet updated successfully
    - application/json: `Pet`
  - **400**: Invalid data supplied
    - application/json: `ErrorResponse`
  - **404**: Pet not found
    - application/json: `ErrorResponse`

### DELETE /pets/{petId}
- operationId: "deletePet"
- summary: "Delete a pet"
- description: "Permanently removes a pet from the store inventory. This action cannot be undone."
- tags: ["Pets"]
- Security: Inherits global security
- Parameters:
  - **petId** (path, required): integer (int64)
    - Description: Unique identifier of the pet to delete
- Request body:
  - (none)
- Responses:
  - **204**: Pet deleted successfully — no content returned
  - **404**: Pet not found
    - application/json: `ErrorResponse`

### PATCH /pets/{petId}
- operationId: "patchPet"
- summary: "Partially update a pet"
- description: "Updates one or more fields of an existing pet without requiring the full object."
- tags: ["Pets"]
- Security: Inherits global security
- Parameters:
  - **petId** (path, required): integer (int64)
- Request body:
  - required
    - application/json: `PatchPetRequest`
- Responses:
  - **200**: Pet patched successfully
    - application/json: `Pet`
  - **404**: Pet not found
    - application/json: `ErrorResponse`

### POST /orders
- operationId: "placeOrder"
- summary: "Place an order"
- description: "Places a new order for one or more pets. Validates pet availability before confirming."
- tags: ["Orders"]
- Security: Inherits global security
- Parameters:
  - (none)
- Request body:
  - required
    - application/json: `CreateOrderRequest`
- Responses:
  - **201**: Order placed successfully
    - application/json: `Order`
  - **400**: Invalid order data or pet unavailable
    - application/json: `ErrorResponse`
  - **404**: Pet or customer not found
    - application/json: `ErrorResponse`
- Examples:
  - Request body (application/json):
    - {"customerId": 42, "items": [{"petId": 1, "quantity": 1}], "shippingAddress": {"street": "123 Main St", "city": "Springfield", "state": "IL", "zip": "62701", "country": "US"}}

### GET /orders/{orderId}
- operationId: "getOrderById"
- summary: "Get order by ID"
- description: "Returns full order details including line items and shipping information."
- tags: ["Orders"]
- Security: No authentication required
- Parameters:
  - **orderId** (path, required): integer (int64)
- Request body:
  - (none)
- Responses:
  - **200**: Order returned successfully
    - application/json: `Order`
  - **404**: Order not found
    - application/json: `ErrorResponse`

### GET /customers/{customerId}
- operationId: "getCustomerById"
- summary: "Get customer by ID"
- description: "Returns a customer profile. Customers can only access their own profile unless they have ADMIN role."
- tags: ["Customers"]
- Security: Inherits global security
- Parameters:
  - **customerId** (path, required): integer (int64)
  - **X-Correlation-ID** (header, optional): string
- Request body:
  - (none)
- Responses:
  - **200**: Customer profile returned successfully
    - application/json: `Customer`
  - **403**: Forbidden - cannot access another customer's profile
    - application/json: `ErrorResponse`
  - **404**: Customer not found
    - application/json: `ErrorResponse`

## Schemas

### BaseEntity
- Description: Base fields shared by all entities
- Type: object
- Properties:
  - **id**: integer (int64) *(required)*
    - Description: Auto-generated unique identifier
    - Example: 1
  - **createdAt**: string (date-time)
    - Description: ISO 8601 timestamp of creation
    - Example: "2026-01-01T00:00:00Z"
  - **updatedAt**: string (date-time)
    - Description: ISO 8601 timestamp of last update
    - Example: "2026-01-15T12:00:00Z"

### Pet
- Composition: allOf
  - extends `BaseEntity`
  - inline extends:
    - Description: A pet available in the store
    - Type: object
    - Properties:
      - **name**: string *(required)*
        - Description: Pet name
        - Example: "Buddy"
      - **species**: string *(required)*
        - Description: Animal species
        - Enum: "dog", "cat", "bird", "rabbit", "fish", "other"
        - Example: "dog"
      - **breed**: string
        - Description: Breed of the animal
        - Example: "Labrador"
      - **age**: integer
        - Description: Age in years
        - Constraints: minimum=0, maximum=30
        - Example: 3
      - **price**: number (float) *(required)*
        - Description: Sale price in USD
        - Constraints: minimum=0
        - Example: 299.99
      - **status**: string *(required)*
        - Description: Current availability status
        - Enum: "available", "pending", "sold"
        - Example: "available"
      - **tags**: array of string
        - Description: Descriptive tags for the pet
        - Example: ["friendly", "vaccinated"]
        - Items:
          - Type: string
      - **medicalRecord**: `MedicalRecord`
      - **owner**: composed schema
        - Composition: oneOf
          - option `Customer`
          - inline option:
            - Type: object
            - Properties:
              - **storeName**: string
                - Description: Name of the store currently holding the pet
        - Description: Current owner — either a Customer or the store itself

### MedicalRecord
- Description: Medical history and vaccination records for a pet
- Type: object
- Properties:
  - **vaccinated**: boolean
    - Description: Whether the pet is fully vaccinated
    - Example: true
  - **neutered**: boolean
    - Description: Whether the pet is neutered/spayed
    - Example: false
  - **lastCheckup**: string (date)
    - Description: Date of last veterinary checkup
    - Example: "2026-03-15"
  - **conditions**: array of string
    - Description: List of known medical conditions
    - Example: ["hip dysplasia"]
    - Items:
      - Type: string
  - **veterinarian**: `Veterinarian`

### Veterinarian
- Description: Veterinarian assigned to a pet
- Type: object
- Properties:
  - **id**: integer (int64)
    - Description: Vet ID
    - Example: 10
  - **name**: string
    - Description: Full name of the veterinarian
    - Example: "Dr. Sarah Johnson"
  - **clinic**: string
    - Description: Clinic name
    - Example: "Happy Paws Clinic"

### Customer
- Composition: allOf
  - extends `BaseEntity`
  - inline extends:
    - Description: A registered customer of the pet store
    - Type: object
    - Properties:
      - **firstName**: string *(required)*
        - Description: Customer first name
        - Example: "Jane"
      - **lastName**: string *(required)*
        - Description: Customer last name
        - Example: "Doe"
      - **email**: string (email) *(required)*
        - Description: Customer email address
        - Example: "jane.doe@example.com"
      - **phone**: string
        - Description: Customer phone number
        - Example: "+1-555-0100"
      - **address**: `Address`

### Address
- Description: Physical address
- Type: object
- Properties:
  - **street**: string *(required)*
    - Description: Street address
    - Example: "123 Main St"
  - **city**: string *(required)*
    - Description: City name
    - Example: "Springfield"
  - **state**: string
    - Description: State or province code
    - Example: "IL"
  - **zip**: string
    - Description: Postal/ZIP code
    - Example: "62701"
  - **country**: string *(required)*
    - Description: ISO 3166-1 alpha-2 country code
    - Example: "US"

### Order
- Composition: allOf
  - extends `BaseEntity`
  - inline extends:
    - Description: A customer order for one or more pets
    - Type: object
    - Properties:
      - **customerId**: integer (int64) *(required)*
        - Description: ID of the customer who placed the order
        - Example: 42
      - **status**: string *(required)*
        - Description: Current order status
        - Enum: "pending", "confirmed", "shipped", "delivered", "cancelled"
        - Example: "confirmed"
      - **items**: array of `OrderItem` *(required)*
        - Description: Line items in the order
      - **shippingAddress**: `Address` *(required)*
      - **totalAmount**: number (float)
        - Description: Total order amount in USD
        - Example: 299.99
      - **payment**: composed schema
        - Composition: anyOf
          - option `CreditCardPayment`
          - option `BankTransferPayment`
        - Description: Payment details — either credit card or bank transfer

### OrderItem
- Description: A single line item in an order
- Type: object
- Properties:
  - **petId**: integer (int64) *(required)*
    - Description: ID of the pet being ordered
    - Example: 1
  - **quantity**: integer *(required)*
    - Description: Number of units
    - Constraints: minimum=1
    - Example: 1
  - **unitPrice**: number (float) *(required)*
    - Description: Price per unit at time of order
    - Example: 299.99

### CreditCardPayment
- Description: Credit card payment details
- Type: object
- Properties:
  - **type**: string *(required)*
    - Enum: "credit_card"
    - Example: "credit_card"
  - **last4**: string *(required)*
    - Description: Last 4 digits of the card
    - Example: "4242"
  - **brand**: string *(required)*
    - Description: Card brand
    - Enum: "visa", "mastercard", "amex", "discover"
    - Example: "visa"
  - **expiryMonth**: integer
    - Constraints: minimum=1, maximum=12
    - Example: 12
  - **expiryYear**: integer
    - Constraints: minimum=2024
    - Example: 2028

### BankTransferPayment
- Description: Bank transfer payment details
- Type: object
- Properties:
  - **type**: string *(required)*
    - Enum: "bank_transfer"
    - Example: "bank_transfer"
  - **bankName**: string *(required)*
    - Description: Name of the bank
    - Example: "Chase"
  - **accountLast4**: string *(required)*
    - Description: Last 4 digits of the bank account
    - Example: "6789"

### CreatePetRequest
- Description: Request body for creating a new pet
- Type: object
- Properties:
  - **name**: string *(required)*
    - Description: Pet name
    - Example: "Max"
  - **species**: string *(required)*
    - Enum: "dog", "cat", "bird", "rabbit", "fish", "other"
    - Example: "dog"
  - **breed**: string
    - Example: "Golden Retriever"
  - **age**: integer
    - Constraints: minimum=0
    - Example: 2
  - **price**: number (float) *(required)*
    - Constraints: minimum=0
    - Example: 499.99
  - **status**: string *(required)*
    - Enum: "available", "pending", "sold"
    - Example: "available"
  - **tags**: array of string
    - Example: ["friendly", "trained"]
    - Items:
      - Type: string

### UpdatePetRequest
- Description: Request body for full pet update — all fields required
- Type: object
- Properties:
  - **name**: string *(required)*
    - Example: "Buddy Updated"
  - **species**: string *(required)*
    - Enum: "dog", "cat", "bird", "rabbit", "fish", "other"
  - **breed**: string
  - **age**: integer
    - Constraints: minimum=0
  - **price**: number (float) *(required)*
    - Constraints: minimum=0
  - **status**: string *(required)*
    - Enum: "available", "pending", "sold"

### PatchPetRequest
- Description: Request body for partial pet update — all fields optional
- Type: object
- Properties:
  - **name**: string
  - **price**: number (float)
    - Constraints: minimum=0
  - **status**: string
    - Enum: "available", "pending", "sold"
  - **tags**: array of string
    - Items:
      - Type: string

### CreateOrderRequest
- Description: Request body for placing a new order
- Type: object
- Properties:
  - **customerId**: integer (int64) *(required)*
    - Example: 42
  - **items**: array of `OrderItem` *(required)*
  - **shippingAddress**: `Address` *(required)*

### PetListResponse
- Description: Paginated response wrapper for pet listings
- Type: object
- Properties:
  - **data**: array of `Pet`
  - **total**: integer
    - Description: Total number of pets matching the filter
    - Example: 42
  - **page**: integer
    - Description: Current page number
    - Example: 1
  - **pageSize**: integer
    - Description: Number of items per page
    - Example: 20

### ErrorResponse
- Description: Standard error response
- Type: object
- Properties:
  - **code**: string *(required)*
    - Description: Machine-readable error code
    - Example: "INVALID_INPUT"
  - **message**: string *(required)*
    - Description: Human-readable error message
    - Example: "The supplied pet ID is invalid"
  - **details**: array of object
    - Description: Additional error detail objects
    - Items:
      - Type: object
      - Properties:
        - **field**: string
          - Example: "price"
        - **issue**: string
          - Example: "must be greater than 0"

### GhostSchema
- ⚠️ unresolvable $ref → #/components/schemas/DoesNotExist

### DoesNotExist
- ⚠️ unresolvable $ref → #/components/schemas/DoesNotExist

## User Stories

(none provided)

## Warnings

- Unresolvable $ref: $.components.schemas.GhostSchema -> #/components/schemas/DoesNotExist

## Broken $ref Summary

- Total broken $ref occurrences: 1
- Affected endpoints: 0