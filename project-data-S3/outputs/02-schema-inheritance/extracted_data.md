# Extracted API Data

## Metadata

- Title: "Fleet API"
- Version: "1.0.0"
- Description: "Tests allOf-based schema composition/inheritance, two levels deep."
- Contact: null
- License: null
- Servers: []
- Tags: []

## Security

- Global requirements: []
- Schemes:
  - none

## Endpoints

### GET /vehicles
- operationId: "listVehicles"
- summary: null
- description: null
- tags: []
- security: null
- Parameters:
  - (none)
- Request body:
  - (none)
- Responses:
  - **200**: All vehicles
    - application/json: array of `Vehicle`

### GET /vehicles/cars
- operationId: "listCars"
- summary: null
- description: null
- tags: []
- security: null
- Parameters:
  - (none)
- Request body:
  - (none)
- Responses:
  - **200**: All cars
    - application/json: array of `Car`

### GET /vehicles/sports-cars
- operationId: "listSportsCars"
- summary: null
- description: null
- tags: []
- security: null
- Parameters:
  - (none)
- Request body:
  - (none)
- Responses:
  - **200**: All sports cars
    - application/json: array of `SportsCar`

## Schemas

### Vehicle
- Type: object
- Properties:
  - **id**: string *(required)*
  - **make**: string *(required)*
  - **model**: string *(required)*

### Car
- Composition: allOf
  - extends `Vehicle`
  - inline schema:
    - Type: object
    - Properties:
      - **doors**: integer
      - **fuelType**: string
        - Enum: "petrol", "diesel", "electric", "hybrid"

### SportsCar
- Composition: allOf
  - extends `Car`
  - inline schema:
    - Type: object
    - Properties:
      - **topSpeedKph**: number *(required)*
      - **zeroToHundredSeconds**: number

## User Stories

(none provided)

## Warnings

- none

## Broken $ref Summary

- Total broken $ref occurrences: 0
- Affected endpoints: 0