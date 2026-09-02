# Extracted API Data

## Metadata

- Title: "Comments API"
- Version: "1.0.0"
- Description: "Tests a self-referencing schema via array items, a different recursion shape than a direct self-ref property."
- Contact: null
- License: null
- Servers: []
- Tags: []

## Security

- Global requirements: []
- Schemes:
  - none

## Endpoints

### GET /posts/{postId}/comments
- operationId: "listComments"
- summary: null
- description: null
- tags: []
- security: null
- parameters: [{"name": "postId", "in": "path", "required": true, "schema": {"type": "string"}}]
- request_body: null
- responses: {"200": {"description": "Top-level comments, each with nested replies", "content": {"application/json": {"schema": {"type": "array", "items": "Comment"}}}}}

## Schemas

### Comment
```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "string"
    },
    "author": {
      "type": "string"
    },
    "body": {
      "type": "string"
    },
    "replies": {
      "type": "array",
      "items": "Comment"
    }
  },
  "required": [
    "id",
    "author",
    "body"
  ]
}
```

## User Stories

(none provided)

## Warnings

- none

## Broken $ref Summary

- Total broken $ref occurrences: 0
- Affected endpoints: 0