# IOB API Security Matrix

## 1. Token Verification Pipeline
*   **Protocol:** JWT (JSON Web Tokens) with standard symmetric signature verification using HS256.
*   **Validation:** Custom FastAPI dependency checking signature validity and exp field freshness.

## 2. Role-Based Access Control (RBAC)
We enforce fine-grained access rules via RoleChecker dependency injection hooks.
*   operator: Read-only telemetry, alarms, and machines dashboards.
*   admin: Write access to user provisioning and system parameters.

## 3. Secure Transport Headers
Every outbound HTTP response is decorated with headers securing the app against XSS, Framing, Sniffing, and clickjacking attacks:
*   X-Frame-Options: DENY
*   X-Content-Type-Options: nosniff
*   Strict-Transport-Security: max-age=31536000; includeSubDomains