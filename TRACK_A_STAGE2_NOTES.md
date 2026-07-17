# Track A — Stage 2 (Authentication) — Delivery Notes

**Owner:** Hariharan (Track A) · **Scope:** `app/core/security.py`, `app/api/auth.py`
**Status:** ✅ Implemented, integrated with existing Stage 0 / Stage 1 / Stage 5 wiring, and verified offline.

---

## 1. What this ZIP contains (extract over the repo root)

```
track_a_stage2_authentication/
├── app/
│   ├── api/
│   │   └── auth.py                 # [EDIT] Stage-2 login / refresh / me endpoints
│   ├── core/
│   │   ├── security.py             # [EDIT] bcrypt + JWT lifecycle (dual-compatible)
│   │   ├── errors.py               # [NEW]  error_envelope helper used by auth routes
│   │   └── __init__.py             # [EDIT] export hash_password / decode_token / create_refresh_token
│   └── models/
│       └── schemas.py              # [EDIT] add LoginRequest + RefreshRequest DTOs
├── database/
│   └── seed_users.sql              # [NEW]  bcrypt-hashed demo users for local seeds
├── tests/
│   └── test_stage2_auth.py         # [NEW]  Checkpoint-2 offline verification suite
└── TRACK_A_STAGE2_NOTES.md         # this file
```

---

## 2. Stage-2 contract — implemented exactly

| Function / Endpoint | Spec | Status |
|---|---|---|
| `hash_password(plain)` | bcrypt via passlib `CryptContext` | ✅ |
| `verify_password(plain, hash)` | bcrypt verify | ✅ |
| `create_access_token(user_id, role)` | HS256, payload `sub`/`role`/`exp` | ✅ (+ `type=access` for Stage-0) |
| `create_refresh_token(user_id)` | HS256, 7-day, payload `sub`/`type=refresh`/`exp` | ✅ (optional `role` for /refresh) |
| `decode_token(token)` | raises HTTP 401 on JWTError | ✅ |
| `POST /api/v1/auth/login` | credentials → tokens + user profile; 401 via `error_envelope` | ✅ |
| `POST /api/v1/auth/refresh` | refresh → new access; rejects non-refresh tokens | ✅ |
| `GET  /api/v1/auth/me` | `UserContext` + DB lookup | ✅ |

---

## 3. Integration decisions (why dual-compatible signatures)

The Stage-2 prompt writes a *clean* security module, but the live repo already has:

| Consumer | What it expects from `app.core.security` |
|---|---|
| `app/deps.py` (Stage 0) | `verify_token(token) → dict` raising `AuthenticationError` |
| `app/services/auth_service.py` (Phase 5) | `create_access_token(data: dict, expires_delta=…)` / `legacy password hash helper` |
| `app/api/users.py`, `industrial.py`, `dashboard.py` | `get_current_user`, `require_roles`, `require_permissions` |
| Stage-0 tests | `core.security.get_current_user` coexists with `deps.get_current_user` |

**Solution:** keep the Stage-2 *primary* API (string `user_id` + `role`) and accept the Stage 5 dict form via `Union[str, Dict]` overloads. All legacy helpers are preserved. Zero other-track files were broken.

### Config resolution

Settings live in `app.core.config` (`SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `ALGORITHM`). The Stage-2 prompt references `JWT_SECRET_KEY` / `JWT_EXPIRE_MINUTES`. Security resolves both:

```python
_jwt_secret()          → settings.JWT_SECRET_KEY or settings.SECRET_KEY
_access_expire_minutes() → settings.JWT_EXPIRE_MINUTES or settings.ACCESS_TOKEN_EXPIRE_MINUTES
```

### Schemas

`LoginRequest` / `RefreshRequest` are added to `app.models.schemas` (Stage-1 package the prompt imports from). The existing Stage 5 `app.schemas.auth.LoginRequest` is **untouched**.

### error_envelope

New module `app/core/errors.py` (did not exist). Returns a structured `HTTPException` whose `detail` is:

```json
{ "error_code": "INVALID_CREDENTIALS", "message": "Email or password is incorrect" }
```

401 responses include `WWW-Authenticate: Bearer`.

---

## 4. Demo users (seed)

| Email | Password | Role |
|---|---|---|
| `admin@iob.demo` | `admin123` | admin |
| `engineer@iob.demo` | `engineer123` | engineer |
| `operator@iob.demo` | `operator123` | operator |

Apply with:

```bash
psql "$DATABASE_URL" -f database/seed_users.sql
```

---

## 5. Verification (Checkpoint 2)

### Offline suite (no Postgres required)

```bash
export SECRET_KEY="test-secret-key-for-stage2-auth-at-least-32-chars"
export DATABASE_URL="sqlite:///./test_stage2.db"
pytest tests/test_stage2_auth.py -v
```

### Live curl (requires running API + seeded Postgres)

```bash
# 1. Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"email": "admin@iob.demo", "password": "admin123"}'

# 2. /me authenticated
curl -X GET "http://localhost:8000/api/v1/auth/me" \
     -H "Authorization: Bearer <PASTE_ACCESS_TOKEN>"

# 3. /me unauthenticated → 401
curl -X GET "http://localhost:8000/api/v1/auth/me"
```

---

## 6. Ownership boundary

| File | Action | Owner |
|---|---|---|
| `app/core/security.py` | EDIT | Track A Stage 2 |
| `app/api/auth.py` | EDIT | Track A Stage 2 |
| `app/core/errors.py` | NEW (required by auth.py import) | Track A Stage 2 glue |
| `app/models/schemas.py` | EDIT (additive DTOs only) | Track A Stage 2 glue |
| `app/core/__init__.py` | EDIT (exports only) | Track A Stage 2 glue |
| `database/seed_users.sql` | NEW | Track A Stage 2 |
| `tests/test_stage2_auth.py` | NEW | Track A Stage 2 |
| `app/deps.py` | **NOT TOUCHED** | Stage 0 |
| `app/database.py` / models ORM | **NOT TOUCHED** | Stage 1 |
| Stage 5 services / other routers | **NOT TOUCHED** | other tracks |
