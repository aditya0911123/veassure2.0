# Extracted API Data

## Metadata

- Title: "Bookstore API"
- Version: "1.0.0"
- Description: "A small, plain CRUD API with no composition, no broken refs, no recursion."
- Contact: (none)
- License: (none)
- Servers:
  - https://api.example.com/v1
- Tags:
  - books — Book catalog operations

## Security

- Global requirements:
  - (none)
- Schemes:
  - (none)

## Endpoints

### GET /books
- operationId: "listBooks"
- summary: "List all books"
- description: null
- tags: ["books"]
- Security: Inherits global security
- Parameters:
  - (none)
- Request body:
  - (none)
- Responses:
  - **200**: A list of books
    - application/json: array of `Book`

### POST /books
- operationId: "createBook"
- summary: "Create a new book"
- description: null
- tags: ["books"]
- Security: Inherits global security
- Parameters:
  - (none)
- Request body:
  - required
    - application/json: `BookInput`
- Responses:
  - **201**: Book created
    - application/json: `Book`

### GET /books/{bookId}
- operationId: "getBook"
- summary: "Get a single book"
- description: null
- tags: ["books"]
- Security: Inherits global security
- Parameters:
  - **bookId** (path, required): string
- Request body:
  - (none)
- Responses:
  - **200**: The book
    - application/json: `Book`
  - **404**: Book not found

### DELETE /books/{bookId}
- operationId: "deleteBook"
- summary: "Delete a book"
- description: null
- tags: ["books"]
- Security: Inherits global security
- Parameters:
  - **bookId** (path, required): string
- Request body:
  - (none)
- Responses:
  - **204**: Book deleted

## Schemas

### Book
- Type: object
- Properties:
  - **id**: string *(required)*
  - **title**: string *(required)*
  - **author**: string *(required)*
  - **publishedYear**: integer
    - Constraints: minimum=1450

### BookInput
- Type: object
- Properties:
  - **title**: string *(required)*
  - **author**: string *(required)*
  - **publishedYear**: integer
    - Constraints: minimum=1450

## User Stories

As a shopper, I want to see a list of all books so that I can browse the catalog.
As a shopper, I want to view a single book's details before buying it.
As an admin, I want to add new books to the catalog.
As an admin, I want to remove books that are no longer sold.

