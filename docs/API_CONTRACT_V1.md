# IOB API Contract — v1

All API errors use a stable JSON envelope.

## Validation failure (HTTP 422)

```json
{
  "success": false,
  "error": "VALIDATION_ERROR",
  "message": "The request payload or parameter format is invalid.",
  "details": [
    {"type": "missing", "loc": ["body", "asset_id"], "msg": "Field required", "input": null}
  ]
}
```

## Database unavailable (HTTP 503)

```json
{
  "success": false,
  "error": "DATABASE_UNAVAILABLE",
  "message": "Persistent storage engine is temporarily unable to fulfill the request.",
  "details": []
}
```

## Canonical routes

Asset tracking is exposed only under `/api/v1/assets/*`. Alert operations are
exposed under `/api/v1/alerts/*`. The retired `/api/v1/industrial/*` aliases are
not registered.
