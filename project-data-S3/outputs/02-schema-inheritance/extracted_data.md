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
- parameters: []
- request_body: null
- responses: {"200": {"description": "All vehicles", "content": {"application/json": {"schema": {"type": "array", "items": "Vehicle"}}}}}

### GET /vehicles/cars
- operationId: "listCars"
- summary: null
- description: null
- tags: []
- security: null
- parameters: []
- request_body: null
- responses: {"200": {"description": "All cars", "content": {"application/json": {"schema": {"type": "array", "items": "Car"}}}}}

### GET /vehicles/sports-cars
- operationId: "listSportsCars"
- summary: null
- description: null
- tags: []
- security: null
- parameters: []
- request_body: null
- responses: {"200": {"description": "All sports cars", "content": {"application/json": {"schema": {"type": "array", "items": "SportsCar"}}}}}

## Schemas

### Vehicle
```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "string"
    },
    "make": {
      "type": "string"
    },
    "model": {
      "type": "string"
    }
  },
  "required": [
    "id",
    "make",
    "model"
  ]
}
```

### Car
```json
{
  "allOf": [
    "Vehicle",
    {
      "type": "object",
      "properties": {
        "doors": {
          "type": "integer"
        },
        "fuelType": {
          "type": "string",
          "enum": [
            "petrol",
            "diesel",
            "electric",
            "hybrid"
          ]
        }
      }
    }
  ]
}
```

### SportsCar
```json
{
  "allOf": [
    "Car",
    {
      "type": "object",
      "properties": {
        "topSpeedKph": {
          "type": "number"
        },
        "zeroToHundredSeconds": {
          "type": "number"
        }
      },
      "required": [
        "topSpeedKph"
      ]
    }
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