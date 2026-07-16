# Track A Stage 2 — Install

Extract this folder **over the repo root** of `hackbrain` (paths already match):

```bash
cd /path/to/hackbrain
unzip track_a_stage2_authentication.zip
# or:
cp -R track_a_stage2_authentication/* .
```

## Files written

| Path | Action |
|------|--------|
| `app/core/security.py` | EDIT — bcrypt + JWT (Stage-2 + Stage 5 dual API) |
| `app/api/auth.py` | EDIT — `/login`, `/refresh`, `/me` |
| `app/core/errors.py` | NEW — `error_envelope` |
| `app/core/__init__.py` | EDIT — exports |
| `app/models/schemas.py` | EDIT — `LoginRequest`, `RefreshRequest` |
| `app/schemas/auth.py` | FIX — pre-existing syntax error (`for v` → `for c in v`) |
| `database/seed_users.sql` | NEW — bcrypt demo users |
| `tests/test_stage2_auth.py` | NEW — Checkpoint 2 suite |
| `TRACK_A_STAGE2_NOTES.md` | NEW — delivery notes |

## Seed demo users

```bash
psql "$DATABASE_URL" -f database/seed_users.sql
```

| Email | Password | Role |
|-------|----------|------|
| admin@iob.demo | admin123 | admin |
| engineer@iob.demo | engineer123 | engineer |
| operator@iob.demo | operator123 | operator |

## Checkpoint 2 curls

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@iob.demo","password":"admin123"}'

curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"

curl -X GET "http://localhost:8000/api/v1/auth/me"   # expect 401
```
