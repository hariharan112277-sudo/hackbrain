# Authentication

Phase 4 uses JWT bearer tokens for stateless authentication.

## Login Flow

1. Client POSTs credentials to `/api/v1/auth/login` using `application/x-www-form-urlencoded`.
2. Server validates credentials and returns an access token and refresh token.
3. Client includes the access token in the `Authorization: Bearer <token>` header.

## Default Test Account

| Username | Password | Roles |
|----------|----------|-------|
| `admin` | `SecurePass123!` | admin, operator |

> Change the default password before deploying to production.

## Token Configuration

- **Access token TTL:** `ACCESS_TOKEN_EXPIRE_MINUTES` (default 30 minutes)
- **Refresh token TTL:** `REFRESH_TOKEN_EXPIRE_DAYS` (default 7 days)
- **Algorithm:** HS256
- **Secret:** `SECRET_KEY` environment variable

## Role-Based Access

- `admin`: full user management and alarm resolution
- `operator`: alarm resolution, read-only industrial data
- Unauthenticated requests receive `401 Unauthorized`.
- Authenticated requests without required roles receive `403 Forbidden`.

## Swagger / OpenAPI

The OpenAPI docs at `/api/v1/docs` include an **Authorize** button powered by the OAuth2 password flow.
