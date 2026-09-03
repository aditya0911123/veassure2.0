# Extracted API Data

## Metadata

- Title: "Comments API"
- Version: "1.0.0"
- Description: "Tests a self-referencing schema via array items, a different recursion shape than a direct self-ref property."
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

### GET /posts/{postId}/comments
- operationId: "listComments"
- summary: null
- description: null
- tags: []
- Security: Inherits global security
- Parameters:
  - **postId** (path, required): string
- Request body:
  - (none)
- Responses:
  - **200**: Top-level comments, each with nested replies
    - application/json: array of `Comment`

## Schemas

### Comment
- Type: object
- Properties:
  - **id**: string *(required)*
  - **author**: string *(required)*
  - **body**: string *(required)*
  - **replies**: array of `Comment`

## User Stories

(none provided)
