"""Small schema checks. Stdlib only so a fresh checkout can test without pip."""

from __future__ import annotations

import json
from pathlib import Path

SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"


def load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text())


def _fail(errors: list[str], path: str, message: str) -> None:
    errors.append(f"{path}: {message}")


def validate(instance, schema: dict, path: str = "$") -> list[str]:
    errors: list[str] = []
    expected = schema.get("type")
    if expected == "object":
        if not isinstance(instance, dict):
            return [f"{path}: expected object"]
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                _fail(errors, path, f"missing {key}")
        if schema.get("additionalProperties") is False:
            allowed = set(schema.get("properties", {}))
            for key in instance:
                if key not in allowed:
                    _fail(errors, f"{path}.{key}", "unexpected property")
        for key, sub in schema.get("properties", {}).items():
            if key in instance:
                errors.extend(validate(instance[key], sub, f"{path}.{key}"))
        return errors
    if expected == "array":
        if not isinstance(instance, list):
            return [f"{path}: expected array"]
        if "minItems" in schema and len(instance) < schema["minItems"]:
            _fail(errors, path, "too few items")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(instance):
                errors.extend(validate(item, item_schema, f"{path}[{index}]"))
        return errors
    if isinstance(expected, list):
        if not any(_type_ok(instance, item) for item in expected):
            return [f"{path}: expected one of {expected}"]
        return errors
    if expected and not _type_ok(instance, expected):
        return [f"{path}: expected {expected}"]
    if "enum" in schema and instance not in schema["enum"]:
        _fail(errors, path, f"not in {schema['enum']}")
    if "minimum" in schema and isinstance(instance, (int, float)) and instance < schema["minimum"]:
        _fail(errors, path, "below minimum")
    if "maximum" in schema and isinstance(instance, (int, float)) and instance > schema["maximum"]:
        _fail(errors, path, "above maximum")
    return errors


def _type_ok(instance, expected: str) -> bool:
    if expected == "string":
        return isinstance(instance, str)
    if expected == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if expected == "number":
        return isinstance(instance, (int, float)) and not isinstance(instance, bool)
    if expected == "boolean":
        return isinstance(instance, bool)
    if expected == "null":
        return instance is None
    if expected == "object":
        return isinstance(instance, dict)
    if expected == "array":
        return isinstance(instance, list)
    return False
