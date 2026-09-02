"""Builds the 'schemas' section of extracted_data.json from
components.schemas. Every schema's own type/format/properties/constraints/
examples/required/enum content comes through build_clean_view: concrete
values are sourced from prance's resolved spec, while any nested $ref to
another named schema (composition via allOf/oneOf/anyOf, or a property
typed as another schema) collapses to that schema's bare name instead of
being inlined or expanded.
"""

from __future__ import annotations

from typing import Any

from .ref_resolution import build_clean_view


def extract_schemas(
    raw_spec: dict[str, Any], resolved_spec: dict[str, Any], warnings: list[str]
) -> dict[str, Any]:
    raw_schemas = raw_spec.get("components", {}).get("schemas", {})
    resolved_schemas = resolved_spec.get("components", {}).get("schemas", {})

    schemas: dict[str, Any] = {}
    for name, definition in raw_schemas.items():
        schemas[name] = build_clean_view(
            definition,
            resolved_schemas.get(name),
            raw_spec,
            f"components.schemas.{name}",
            warnings,
        )
    return schemas
