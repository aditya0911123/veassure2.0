# Extracted API Data

## Metadata

- Title: "Search API"
- Version: "1.0.0"
- Description: "Tests path-level shared parameters merged with operation-level parameters across all 'in' locations, plus multiple response codes."
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

### GET /search/{index}
- operationId: "search"
- summary: null
- description: null
- tags: []
- Security: Inherits global security
- Parameters:
  - **index** (path, required): string
    - Description: Shared across every method on this path
  - **X-Request-Id** (header, optional): string
    - Description: Also shared - a path-level header parameter
  - **q** (query, required): string
  - **limit** (query, optional): integer
  - **session** (cookie, optional): string
- Request body:
  - (none)
- Responses:
  - **200**: Search results
    - application/json: `SearchResults`
  - **400**: Invalid query
    - application/json: `Error`
  - **404**: Index not found
    - application/json: `Error`
  - **500**: Internal error
    - application/json: `Error`

## Schemas

### SearchResults
- Type: object
- Properties:
  - **total**: integer *(required)*
  - **items**: array of object *(required)*
    - Items:
      - Type: object

### Error
- Type: object
- Properties:
  - **code**: string *(required)*
  - **message**: string *(required)*

## User Stories

(none provided)
