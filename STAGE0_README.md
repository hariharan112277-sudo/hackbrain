# Stage 0 — Dependency Layer (Track A / Hariharan)

## Summary

This delivery implements the **authentication security context** and **role-based access control (RBAC)** helpers in `app/deps.py`, completing **Stage 0 (Dependency Layer)** of the Industrial Operating Brain (IOB) project.

---

## File Changed

| File | Status | Description |
|------|--------|-------------|
| `app/deps.py` | **EDITED** | Added auth context + RBAC on top of existing DB session re-exports |

## New File

| File | Status | Description |
|------|--------|-------------|
| `tests/test_deps_stage0.py` | **NEW** | 24 verification tests for Stage 0 |

---

## What Was Added to `app/deps.py`

### 1. Preserved (Existing)
- `get_db` — re-exported from `app.database`
- `DBSession` — `Annotated[Session, Depends(get_db)]` alias

### 2. New: OAuth2 Token Scheme
```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
```

### 3. New: `UserContext` Class
- Structured identity container with `user_id` and `role`
- Memory-optimized with `__slots__`
- Supports `__eq__`, `__hash__`, `__repr__`

### 4. New: `decode_token()` Function
- Wrapper around `app.core.security.verify_token`
- Converts `AuthenticationError` → `HTTPException(401)`
- Includes `WWW-Authenticate: Bearer` header

### 5. New: `get_current_user()` Dependency
- Extracts JWT from `Authorization: Bearer <token>` header
- Validates `sub` and `role` claims
- Falls back to `roles` list (backward-compatible with existing tokens)
- Returns `UserContext` instance

### 6. New: `require_role()` RBAC Factory
- Dependency factory for role-gated endpoints
- Raises `HTTPException(403)` on insufficient role
- Returns `UserContext` on success

---

## Integration Notes

### How It Integrates With Existing Wiring

| Module | Integration Point |
|--------|------------------|
| `app/core/security.py` | `decode_token()` wraps `verify_token()` from this module |
| `app/core/exceptions.py` | `decode_token()` catches `AuthenticationError` |
| `app/database.py` | Existing `get_db` is preserved and re-exported |
| `app/api/auth.py` | Login endpoint at `/api/v1/auth/login` matches `oauth2_scheme.tokenUrl` |

### Backward Compatibility
- The existing `get_current_user` in `app.core.security` (returns `Dict[str, Any]`) **coexists** with the new `get_current_user` in `app.deps` (returns `UserContext`) — no conflicts
- Tokens with `"roles": ["admin"]` (list) are handled via fallback to extract the first role
- Existing `DBSession` and `get_db` imports continue working unchanged

### Downstream Dependency: Track B (Lathika)
⚠️ **Track B cannot build or verify `app/api/ws.py` WebSocket authentication until this file is merged.**

Lathika should import from this module:
```python
from app.deps import get_current_user, UserContext, require_role
```

---

## Verification (Checkpoint 0)

Run the test suite:
```bash
export SECRET_KEY="your-secret-key-at-least-32-chars"
export DATABASE_URL="sqlite:///./test.db"
export ALGORITHM="HS256"

# Using pytest
pytest tests/test_deps_stage0.py -v

# Or standalone
python tests/test_deps_stage0.py
```

**All 24 tests pass:**
- 5 module structure tests
- 6 UserContext tests  
- 4 decode_token tests
- 5 get_current_user tests
- 4 require_role tests

---

## Git Commit Convention

```
[hariharan][stage0] implement dependencies in deps.py
```

Branch: `backend/core-api`

---

## Usage Examples

### Basic Authentication
```python
from fastapi import APIRouter, Depends
from app.deps import get_current_user, UserContext

router = APIRouter()

@router.get("/profile")
def get_profile(user: UserContext = Depends(get_current_user)):
    return {"user_id": user.user_id, "role": user.role}
```

### Role-Gated Endpoint
```python
from app.deps import require_role, UserContext

@router.delete("/machines/{machine_id}")
def remove_machine(
    machine_id: str,
    user: UserContext = Depends(require_role("admin", "supervisor")),
):
    ...
```

### Combined with Database Session
```python
from app.deps import DBSession, get_current_user, UserContext

@router.get("/dashboard")
def dashboard(db: DBSession, user: UserContext = Depends(get_current_user)):
    ...
```
