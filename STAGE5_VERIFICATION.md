# Stage 5 Migration Bundle

Base repository: `hariharan112277-sudo/hackbrain`

Base commit: `486e5a00560c92428e68ef8da27f49da97accfa3`

## Apply

Copy the contents of this directory over the root of the matching repository,
preserving the included relative paths.

## Implemented

- Unified bcrypt password API and removal of the deprecated hash alias.
- Production boot validation for JWT, MQTT, and database secrets.
- Hard prevention of volatile repository providers in production.
- Dynamic development/production user repository selection.
- Persistent SQLAlchemy user repository and immutable authorization policy adapters.
- FastAPI lifecycle bootstrap and repository shutdown wiring.
- Downstream auth/user service migration to `hash_password`.
- Test context setup and migration regression tests.
- Repaired TOML/dependency constraints needed to execute pytest reliably.

## Verification

- Forbidden legacy-token scans: **0 occurrences** for both requested patterns.
- Python compile check: **PASS**.
- TOML parse check: **PASS**.
- Focused authentication, contracts, database dependency, and migration matrix:
  **82 passed / 82 collected**.
- Requested complete legacy-suite command was also executed. Result:
  **153 passed, 56 failed, 6 setup errors**. The remaining failures belong to
  incompatible pre-existing API generations (username-based in-memory routes,
  service-based routes, and older core logging/health contracts) outside this
  migration's targeted modules. They are recorded here rather than represented
  as a successful full-suite run.
