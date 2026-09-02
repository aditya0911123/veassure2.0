# Extracted API Data

## Metadata

- Title: "User Management API"
- Version: "1.0.0"
- Description: "API for managing users - create, update, delete, and query user profiles."
- Contact: {"name": "API Support", "email": "support@example.com"}
- License: {"name": "Apache 2.0", "url": "http://www.apache.org/licenses/LICENSE-2.0"}
- Servers: [{"url": "http://localhost:8080", "description": "Local development server"}]
- Tags: [{"name": "User Management", "description": "Operations for creating and managing user accounts"}]

## Security

- Global requirements: [{"BearerAuth": []}]
- Schemes:
  - BearerAuth: {"type": "http", "scheme": "bearer", "bearerFormat": "JWT", "description": "JWT Authorization header. Example: Authorization: Bearer <token>"}

## Endpoints

### GET /api/v1/private/user/profile
- operationId: "getAuthUser"
- summary: "Get authenticated user profile"
- description: "Returns the full profile of the currently authenticated user, derived from the JWT Bearer token. The response includes computed fields such as groups (with IDs), permissions, loginTime, and lastAccess. Sensitive fields such as password and repeatPassword are never returned."
- tags: ["User Management"]
- security: [{"BearerAuth": []}]
- Parameters:
  - **lang** (query, optional): string
    - Description: Two-letter language code for the response locale, e.g. en, fr
- Request body:
  - (none)
- Responses:
  - **200**: Authenticated user profile returned successfully
    - application/json: `ReadableUser`
  - **401**: Unauthorized - no Authorization header or Bearer token was provided in the request
    - application/json: `ErrorResponse`
  - **500**: Internal Server Error - returned for invalid, expired, tampered, or malformed Bearer token, or unexpected server failures
    - application/json: `ErrorResponse`

## Schemas

### ReadableUser
- Description: User profile returned by the API. Never contains password or repeatPassword fields.
- Type: object
- Properties:
  - **id**: integer (int64)
    - Description: Auto-generated user ID
    - Example: 1
  - **firstName**: string
    - Description: User first name
    - Example: "Administrator"
  - **lastName**: string
    - Description: User last name
    - Example: "User"
  - **emailAddress**: string (email)
    - Description: User email address
    - Example: "admin@shopizer.com"
  - **defaultLanguage**: string
    - Description: Two-letter ISO 639-1 language code
    - Example: "en"
  - **userName**: string
    - Description: Unique username / login name
    - Example: "admin@shopizer.com"
  - **active**: boolean
    - Description: Whether the account is active
    - Example: true
  - **lastAccess**: string (date-time)
    - Description: ISO 8601 timestamp of last API access. Null for newly created users
  - **loginTime**: string (date-time)
    - Description: ISO 8601 timestamp of last login. Null for newly created users
  - **merchant**: string
    - Description: Store / merchant code - corresponds to the store field sent on create
    - Example: "DEFAULT"
  - **permissions**: array of `ReadablePermission`
    - Description: Permissions computed as the union of all permissions from the user assigned groups
  - **groups**: array of `ReadableGroup`
    - Description: Groups assigned to the user, enriched with IDs from the system. The type field may be null.

### ReadableGroup
- Description: Group / role as returned by the API. The type field is nullable and may be returned as null by the server.
- Type: object
- Properties:
  - **id**: integer (int64)
    - Description: System-assigned group ID
    - Example: 1
  - **name**: string
    - Description: Group name
    - Example: "SUPERADMIN"
  - **type**: string
    - Description: Group type - may be null as returned by the server

### ReadablePermission
- Description: Individual permission entry derived from group membership
- Type: object
- Properties:
  - **id**: integer (int32)
    - Description: System-assigned permission ID
    - Example: 1
  - **name**: string
    - Description: Permission name
    - Example: "AUTH"

### ErrorResponse
- Description: Standard error response returned by the Shopizer API for 401 and 500 errors
- Type: object
- Properties:
  - **timestamp**: string (date-time)
    - Description: ISO 8601 timestamp of when the error occurred
    - Example: "2026-07-16T05:36:32.484+0000"
  - **status**: integer (int32)
    - Description: HTTP status code
    - Example: 401
  - **error**: string
    - Description: Short human-readable error label
    - Example: "Unauthorized"
  - **path**: string
    - Description: The request path that triggered the error
    - Example: "/api/v1/private/user/profile"

## User Stories

(none provided)

## Warnings

- none

## Broken $ref Summary

- Total broken $ref occurrences: 0
- Affected endpoints: 0