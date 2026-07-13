# Enterprise API Lifecycle Management Plan (api_lifecycle.md)

## 1. API Versioning Rules

- **URL Pattern Rule**: All version states must be explicitly declared within the URI framework string layout path, for example `/api/v1/...`.
- **Minor Feature Releases**: Non-breaking structural schema modifications, such as appending optional response tracking fields, must increment minor or patch semantic-version markers without updating the base URI string path.

## 2. Deprecation Framework Rules

When a data contract layout is superseded by structural enhancements:

1. **Response Headers**: The API path handler adds a standard HTTP `Sunset: Date` header accompanied by a tracking `Link: <url>; rel="deprecation"` pointer.
2. **Minimum Lifespan**: Deprecated endpoints must remain functional in the ecosystem for a minimum support window of 180 days before final decommissioning.

## 3. Extensibility Design Guidelines

- **Forward Compatibility**: All response payload objects must reserve a structured root-level `extension_context: dict[str, Any]` field. This allows edge gateways to pass up custom properties without breaking client parsing logic.
- **Polymorphic Payload Handlers**: Pydantic models must use explicit configuration parameters equivalent to `extra="ignore"` to ensure that downstream services discard unrecognized fields during rolling upgrades rather than throwing validation errors.
- **Enum Expansion Governance**: Enum additions require frontend and AI consumer notification before promotion to `active`.
- **Correlation Preservation**: Deprecated and active versions must preserve `X-Correlation-ID` propagation semantics.

## 4. Status Labels

| Label | Meaning |
|---|---|
| `draft` | Proposed but not implementation-ready |
| `frozen-design` | Approved contract; implementation may begin |
| `active` | Implemented and in production use |
| `deprecated` | Supported but scheduled for removal |
| `removed` | No longer available |
