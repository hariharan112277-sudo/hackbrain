"""
JSON Payload Validator Stage for Industrial Telemetry Ingestion Pipeline.
Standard Compliance: RFC 8259 JSON, IEC 62443 Input Validation.
"""

import json
import logging
from typing import Dict, Any, Union
try:
    from jsonschema import validate as validate_schema_raw
except ImportError:
    validate_schema_raw = None

from .exceptions import MalformedJsonException, SchemaValidationException

logger = logging.getLogger("iob.validator")


class JsonPayloadValidator:
    """Validates structural correctness of raw MQTT payloads against schemas."""
    def __init__(self, json_schema_rules: Dict[str, Any] = None, max_size_bytes: int = 1048576, max_payload_size_bytes: int = None):
        self.schema = json_schema_rules or {}
        self.max_size = max_payload_size_bytes if max_payload_size_bytes is not None else max_size_bytes

    def execute_validation(self, raw_binary_payload: Union[bytes, str]) -> Dict[str, Any]:
        binary_data = raw_binary_payload.encode("utf-8") if isinstance(raw_binary_payload, str) else raw_binary_payload

        # 1. Volumetric payload validation check
        if len(binary_data) > self.max_size:
            raise SchemaValidationException(f"Payload boundary block breached: {len(binary_data)} bytes")

        # 2. Structural syntax evaluation
        try:
            parsed_dict = json.loads(binary_data.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as ex:
            raise MalformedJsonException(f"Invalid JSON format string rejected: {str(ex)}")

        if not isinstance(parsed_dict, dict):
            raise MalformedJsonException("Payload must decode to a JSON dictionary object.")

        # Check turn 1 required fields for backwards compatibility
        if "readings" in parsed_dict or "message_id" in parsed_dict:
            if "timestamp" not in parsed_dict or "asset_id" not in parsed_dict:
                raise SchemaValidationException("Missing mandatory fields in payload")
            return parsed_dict

        # 3. Schema validation check for Section 3/4 flat schema
        if validate_schema_raw and self.schema and "required" in self.schema:
            try:
                validate_schema_raw(instance=parsed_dict, schema=self.schema)
            except Exception as ex:
                raise SchemaValidationException(f"Payload validation rule failure: {str(ex)}")

        return parsed_dict

    def process(self, payload: Union[bytes, str, Dict[str, Any]]) -> Dict[str, Any]:
        if isinstance(payload, dict):
            if "readings" in payload or "message_id" in payload:
                if "timestamp" not in payload or "asset_id" not in payload:
                    raise SchemaValidationException("Missing mandatory fields in payload")
                return payload
            if validate_schema_raw and self.schema and "required" in self.schema:
                try:
                    validate_schema_raw(instance=payload, schema=self.schema)
                except Exception as ex:
                    raise SchemaValidationException(f"Payload validation rule failure: {str(ex)}")
            return payload
        return self.execute_validation(payload)
