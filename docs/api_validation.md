# API Validation & Contract Testing
## Phase 5: Schema Validation and OpenAPI Compliance

### Overview

This document describes the API validation strategy for Phase 5, ensuring all endpoints adhere to strict Pydantic schemas and OpenAPI contracts for seamless Member 4 Frontend integration.

### Pydantic Schema Validation

All API endpoints use Pydantic v2 models for request/response validation:

#### Request Validation
```python
# Automatic validation on request body
@router.post("/machines", response_model=MachineResponse)
async def create_machine(machine_data: MachineCreate, ...):
    # machine_data is already validated
    # 422 Unprocessable Entity returned for invalid data
    ...
```

#### Response Validation
```python
# Automatic response serialization and validation
@router.get("/machines/{id}", response_model=MachineResponse)
async def get_machine(machine_id: UUID, ...):
    machine = await service.get_machine(machine_id)
    return MachineResponse(**machine)  # Validated before return
```

### Schema Definitions

#### Machine Schemas
```python
class MachineCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    serial_number: str = Field(..., min_length=1, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    manufacturer: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=255)
    status: MachineStatus = MachineStatus.UNKNOWN
    parent_id: Optional[UUID] = None
    tags: Dict[str, str] = {}

class MachineResponse(MachineCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime
    last_telemetry_at: Optional[datetime]
    
    class Config:
        from_attributes = True  # ORM mode
```

#### Enum Validation
```python
class MachineStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    UNKNOWN = "unknown"

class AlarmSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
```

### Custom Validators

```python
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=12, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)
    
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain special character")
        return v
```

### Error Response Format

All validation errors follow consistent format:

```json
{
  "error": "VALIDATION_ERROR",
  "message": "Input validation failed",
  "details": [
    {
      "field": "password",
      "message": "Password must be at least 12 characters",
      "type": "value_error"
    }
  ]
}
```

### OpenAPI Schema Generation

FastAPI automatically generates OpenAPI 3.0 schema:

```bash
# Access at /openapi.json (when DEBUG=True)
curl http://localhost:8000/openapi.json | jq '.components.schemas.MachineResponse'
```

#### Generated Schema Example
```json
{
  "MachineResponse": {
    "type": "object",
    "required": ["id", "name", "serial_number", "status", "created_at", "updated_at"],
    "properties": {
      "id": {"type": "string", "format": "uuid"},
      "name": {"type": "string", "maxLength": 255},
      "serial_number": {"type": "string", "maxLength": 100},
      "model": {"type": "string", "maxLength": 100, "nullable": true},
      "status": {"$ref": "#/components/schemas/MachineStatus"},
      "created_at": {"type": "string", "format": "date-time"},
      "updated_at": {"type": "string", "format": "date-time"}
    }
  }
}
```

### Contract Testing

#### Schema Compliance Tests
```python
# tests/test_contracts.py
def test_machine_create_schema():
    """Test MachineCreate schema accepts valid data."""
    machine = MachineCreate(
        name="Test Machine",
        serial_number="TM-001",
        status=MachineStatus.ONLINE,
    )
    assert machine.name == "Test Machine"

def test_machine_create_rejects_invalid():
    """Test MachineCreate rejects invalid data."""
    with pytest.raises(ValidationError):
        MachineCreate(name="", serial_number="TM-001")  # Empty name
    
    with pytest.raises(ValidationError):
        MachineCreate(name="Test", serial_number="")  # Empty serial
```

#### Response Contract Tests
```python
@pytest.mark.asyncio
async def test_machine_response_contract(async_client):
    """Test GET /machines/{id} returns valid MachineResponse."""
    response = await async_client.get(f"/api/v1/industrial/machines/{machine_id}")
    assert response.status_code == 200
    
    # Validate against schema
    machine = MachineResponse(**response.json())
    assert isinstance(machine.id, UUID)
    assert machine.status in MachineStatus
```

### Member 4 Integration Checklist

- [ ] All endpoints return `application/json`
- [ ] Response schemas match TypeScript interfaces
- [ ] Enums use string values (not integers)
- [ ] Datetimes in ISO 8601 format (UTC)
- [ ] UUIDs as strings in standard format
- [ ] Pagination uses `page`/`page_size`/`total`/`total_pages`
- [ ] Error responses follow `{error, message, details}` format
- [ ] Field names use snake_case
- [ ] Nullable fields explicitly marked `Optional`

### Generating TypeScript Types

```bash
# Install openapi-typescript
npm install -g openapi-typescript

# Generate types from OpenAPI schema
openapi-typescript http://localhost:8000/openapi.json -o src/types/api.d.ts
```

### Validation Middleware

Custom validation middleware for additional checks:

```python
# app/core/validation_middleware.py
from starlette.middleware.base import BaseHTTPMiddleware

class RequestValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Validate content-type for POST/PUT/PATCH
        if request.method in ("POST", "PUT", "PATCH"):
            content_type = request.headers.get("content-type", "")
            if not content_type.startswith("application/json"):
                return JSONResponse(
                    status_code=415,
                    content={"error": "UNSUPPORTED_MEDIA_TYPE", 
                            "message": "Content-Type must be application/json"}
                )
        return await call_next(request)
```