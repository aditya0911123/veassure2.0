# Extracted API Data

## Metadata

- Title: "User Management API"
- Version: "1.0.0"
- Description: "API for managing users - create, update, delete, and query user profiles."
- Contact: API Support (support@example.com)
- License: Apache 2.0 — http://www.apache.org/licenses/LICENSE-2.0
- Servers:
  - http://localhost:8080 — Local development server
- Tags:
  - User Management — Operations for creating and managing user accounts

## Security

- Global requirements:
  - BearerAuth
- Schemes:
  - **BearerAuth**
    - Type: http
    - Scheme: bearer
    - Bearer format: JWT
    - Description: JWT Authorization header. Example: Authorization: Bearer <token>

## Endpoints

### GET /api/v1/private/user/profile
- operationId: "getAuthUser"
- summary: "Get authenticated user profile"
- description: "Returns the full profile of the currently authenticated user, derived from the JWT Bearer token. The response includes computed fields such as groups (with IDs), permissions, loginTime, and lastAccess. Sensitive fields such as password and repeatPassword are never returned."
- tags: ["User Management"]
- Security:
  - BearerAuth
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
- Examples:
  - Response 200 (application/json):
    - {"id": 1, "firstName": "Administrator", "lastName": "User", "emailAddress": "admin@shopizer.com", "defaultLanguage": "en", "userName": "admin@shopizer.com", "active": true, "lastAccess": null, "loginTime": null, "merchant": "DEFAULT", "permissions": [{"id": 1, "name": "AUTH"}, {"id": 2, "name": "SUPERADMIN"}, {"id": 3, "name": "ADMIN"}, {"id": 4, "name": "PRODUCTS"}, {"id": 5, "name": "ORDER"}, {"id": 6, "name": "CONTENT"}, {"id": 7, "name": "STORE"}, {"id": 8, "name": "TAX"}, {"id": 9, "name": "PAYMENT"}, {"id": 10, "name": "CUSTOMER"}, {"id": 11, "name": "SHIPPING"}], "groups": [{"name": "SUPERADMIN", "type": null, "id": 1}, {"name": "ADMIN", "type": null, "id": 2}]}
  - Response 401 (application/json):
    - {"timestamp": "2026-07-16T05:36:32.484+0000", "status": 401, "error": "Unauthorized", "path": "/api/v1/private/user/profile"}
  - Response 500 (application/json):
    - **invalidToken**: Invalid, tampered, or malformed Bearer token — {"timestamp": "2026-07-16T05:42:59.578+0000", "status": 500, "error": "Internal Server Error", "path": "/api/v1/private/user/profile"}
    - **expiredToken**: Expired JWT Bearer token — {"timestamp": "2026-07-16T05:42:59.578+0000", "status": 500, "error": "Internal Server Error", "path": "/api/v1/private/user/profile"}
    - **unexpectedError**: Unexpected server failure — {"timestamp": "2026-07-16T05:42:59.578+0000", "status": 500, "error": "Internal Server Error", "path": "/api/v1/private/user/profile"}

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
