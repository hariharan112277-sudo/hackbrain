# 9. Machine Metadata Schema

This schema holds the structural asset templates required by downstream applications to determine functional design limits and run-time validation envelopes.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "IOB_Machine_Static_Metadata",
  "type": "object",
  "properties": {
    "machine_id": { "type": "string" },
    "specifications": {
      "type": "object",
      "properties": {
        "power_rating_kw": { "type": "number", "minimum": 0.0 },
        "max_rpm": { "type": "number", "minimum": 0.0 },
        "voltage_requirement_v": { "type": "number" },
        "weight_kg": { "type": "number" }
      },
      "required": ["power_rating_kw", "voltage_requirement_v"]
    },
    "operating_limits": {
      "type": "object",
      "properties": {
        "temperature_range": {
          "type": "object",
          "properties": {
            "min_celsius": { "type": "number" },
            "max_celsius": { "type": "number" }
          },
          "required": ["min_celsius", "max_celsius"]
        },
        "max_pressure_bar": { "type": "number" }
      },
      "required": ["temperature_range"]
    },
    "documentation_references": {
      "type": "object",
      "properties": {
        "schematics_url": { "type": "string", "format": "uri" },
        "maintenance_manual_url": { "type": "string", "format": "uri" },
        "warranty_expiration_date": { "type": "string", "format": "date" }
      },
      "required": ["schematics_url", "maintenance_manual_url"]
    },
    "dependencies": {
      "type": "object",
      "properties": {
        "upstream_machine_id": { "type": "string" },
        "downstream_machine_id": { "type": "string" },
        "required_utilities": {
          "type": "array",
          "items": { "type": "string", "enum": ["COMPRESSED_AIR", "CHILLED_WATER", "THREE_PHASE_POWER", "NATURAL_GAS"] }
        }
      },
      "required": ["required_utilities"]
    }
  },
  "required": ["machine_id", "specifications", "operating_limits", "documentation_references", "dependencies"],
  "additionalProperties": false
}
```