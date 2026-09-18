"""Builds the 'schemas' section of extracted_data.json from
components.schemas. Every schema's own type/format/properties/constraints/
examples/required/enum content comes through build_clean_view: concrete
values are sourced from prance's resolved spec, while any nested $ref to
another named schema (composition via allOf/oneOf/anyOf, or a property
typed as another schema) collapses to that schema's bare name instead of
being inlined or expanded. A $ref that can't safely collapse to a name
(broken, or the loser of a naming conflict) becomes {} - no placeholder
entry is added for it anywhere in this section; the detail lives only in
the broken_refs report returned from extraction, not in this output.

After the internal schemas are extracted, every successfully-resolved
EXTERNAL ref that won its target name (see
resolve_external_schema_placements) gets its actual fetched content added
under that name too - not just a bare-name reference at each usage site,
since otherwise nothing anywhere would define what the name means.
"""

from __future__ import annotations

from typing import Any

from .ref_resolution import build_clean_view, resolve_external_ref_value


def extract_schemas(
    raw_spec: dict[str, Any],
    resolved_spec: dict[str, Any],
    broken_refs: list[dict[str, str]],
    ref_status: dict[str, bool],
    naming_conflicts: dict[str, str],
    external_winners: dict[str, str],
    base_url: str,
    fetch_cache: dict[Any, Any],
) -> dict[str, Any]:
    raw_schemas = raw_spec.get("components", {}).get("schemas", {})
    resolved_schemas = resolved_spec.get("components", {}).get("schemas", {})

    schemas: dict[str, Any] = {}
    for name, definition in raw_schemas.items():
        schemas[name] = build_clean_view(
            definition,
            resolved_schemas.get(name),
            ref_status,
            naming_conflicts,
            f"components.schemas.{name}",
            broken_refs,
        )

    for name, ref in external_winners.items():
        try:
            schemas[name] = resolve_external_ref_value(ref, base_url, fetch_cache)
        except Exception:
            # Already confirmed resolvable by compute_ref_status, so this
            # shouldn't happen - but network/file state can change between
            # that check and this fetch. Degrade gracefully: no entry for
            # this name (nothing to show), and record the late failure for
            # the broken-ref report rather than crash extraction.
            broken_refs.append(
                {"type": "unresolvable", "path": f"components.schemas.{name} (external)", "ref": ref}
            )

    return schemas
