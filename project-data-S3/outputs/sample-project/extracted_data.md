# Extracted API Data

## Metadata

- Title: "Sample API"
- Version: "1.0.0"
- Description: null
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

### GET /pets
- operationId: "listPets"
- summary: null
- description: null
- tags: []
- Security: Inherits global security
- Parameters:
  - (none)
- Request body:
  - (none)
- Responses:
  - **200**: OK
    - application/json: `Pet`

## Schemas

### Pet
- Type: object
- Properties:
  - **id**: integer *(required)*
  - **name**: string *(required)*
  - **friend**: `Pet`

## User Stories

As a user, I want to list all pets so that I can see what's available.
As a user, I want to view a pet's friend relationship.


## Warnings

- none

## Broken $ref Summary

- Total broken $ref occurrences: 0
- Affected endpoints: 0