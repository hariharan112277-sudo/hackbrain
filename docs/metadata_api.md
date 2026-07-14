# Metadata API

Metadata endpoints enrich machine records with asset, sensor, and engineering-unit context.

## GET /api/v1/industrial/machines/{machine_id}/metadata

**Response:**

```json
{
  "success": true,
  "data": {
    "machine_id": "...",
    "machine": { ... },
    "asset": { ... },
    "sensors": [ ... ],
    "engineering_units": {
      "temperature": "CELSIUS",
      "pressure": "BAR",
      "vibration": "MM/S",
      "speed": "RPM"
    },
    "version": "v4.0"
  }
}
```

## Integration Mode Behavior

When `PHASE4_REPOSITORY_MODE=integration`, the adapter delegates to:
- `MetadataIntegrationService.get_entity_metadata`
- `MachineRegistryService.get_machine`
- `SensorRegistryService.list_sensors_by_machine`
- `AssetIntegrationService.get_asset`

This preserves the Member 2 ownership boundary while exposing a unified
metadata resource to the frontend.
