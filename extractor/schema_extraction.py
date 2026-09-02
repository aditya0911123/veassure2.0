"""Builds the 'schemas' section of extracted_data.json from
components.schemas. Every schema's own type/format/properties/constraints/
examples/required/enum content comes through build_clean_view: concrete
values are sourced from prance's resolved spec, while any nested $ref to
another named schema (composition via allOf/oneOf/anyOf, or a property
typed as another schema) collapses to that schema's bare name instead of
being inlined or expanded.

After the resolvable schemas are extracted, the warnings list (already
populated with every broken $ref found anywhere in the document - see
resolve_with_prance) is scanned for any referenced name with no entry of
its own in components.schemas, so a name used at a usage site (e.g. an
endpoint response) but never actually defined still gets a stub entry
here instead of only existing as an inline {"unresolvable": true} marker
at each place it's used.
"""

from __future__ import annotations

from typing import Any

from .ref_resolution import build_clean_view, ref_target_name


def extract_schemas(
    raw_spec: dict[str, Any], resolved_spec: dict[str, Any], warnings: list[str]
) -> dict[str, Any]:
    raw_schemas = raw_spec.get("components", {}).get("schemas", {})
    resolved_schemas = resolved_spec.get("components", {}).get("schemas", {})

    schemas: dict[str, Any] = {}
    for name, definition in raw_schemas.items():
        result = build_clean_view(
            definition,
            resolved_schemas.get(name),
            raw_spec,
            f"components.schemas.{name}",
            warnings,
        )
        # A schema whose entire body is nothing but a broken $ref (e.g.
        # "GhostSchema": {"$ref": "#/components/schemas/DoesNotExist"})
        # comes back from build_clean_view in the inline usage-site marker
        # shape ({"$ref": ..., "unresolvable": true}). At the top level of
        # a named schema entry, normalize that to the same placeholder
        # shape used for a name that's referenced but never defined at all
        # ({"unresolvable": true, "ref": ...}) - one broken-schema shape,
        # not two, at this level. Nested usage sites (a property whose
        # value is a broken ref) keep the original inline marker shape.
        if isinstance(result, dict) and result.get("unresolvable") and "$ref" in result:
            result = {"unresolvable": True, "ref": result["$ref"]}
        schemas[name] = result

    for warning in warnings:
        if not warning.startswith("Unresolvable $ref:"):
            continue
        ref = warning.split(" -> ", 1)[1]
        name = ref_target_name(ref)
        if name not in schemas:
            schemas[name] = {"unresolvable": True, "ref": ref}

    return schemas
