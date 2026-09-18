"""Pure extraction logic: given swagger.json (+ optional userstories.txt),
deterministically extract metadata, security, endpoints, and schemas.

NOTE (migration-handoff): the original file this was copied from also had
an interactive main()/CLI entry point that picked a project folder via
ingestion_service.project_picker and wrote extracted_data.json/.md to disk.
That CLI wiring was stripped here on purpose - an orchestrator agent
supplies the input path itself and decides what to do with the result, so
there's nothing for an interactive project picker to do in this system.
run_extraction() below is the only function meant to be wrapped as a tool.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from .endpoint_extraction import extract_endpoints
from .md_generation import generate_markdown
from .ref_resolution import (
    compute_ref_status,
    find_refs_in,
    resolve_external_schema_placements,
    resolve_with_prance,
)
from .schema_extraction import extract_schemas


def _extract_metadata(spec: dict[str, Any]) -> dict[str, Any]:
    info = spec.get("info", {})
    return {
        "title": info.get("title"),
        "version": info.get("version"),
        "description": info.get("description"),
        "contact": info.get("contact"),
        "license": info.get("license"),
        "servers": spec.get("servers", []),
        "tags": spec.get("tags", []),
    }


def _extract_security(spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "schemes": spec.get("components", {}).get("securitySchemes", {}),
        "global_requirements": spec.get("security", []),
    }


def run_extraction(
    swagger_path: Path,
    userstories_path: Path | None,
    on_prance_resolved: Callable[[dict[str, Any]], None] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, bool], list[dict[str, str]]]:
    """Pure extraction: reads the two input files and returns
    (extracted_data, raw_spec, ref_status, broken_refs). If supplied,
    on_prance_resolved receives Prance's resolved document immediately
    after resolution, allowing a caller to save a review artifact without
    changing the extraction return contract. No interactive I/O beyond
    progress prints - safe to call from a future orchestrator.

    broken_refs is the full detail of every broken/unresolvable ref and
    naming conflict found during extraction - one dict per occurrence,
    each with at least "type" ("unresolvable" | "naming_conflict" |
    "depth_guard") and "path"/"ref" (plus "reason" for naming conflicts).
    It is deliberately NOT written to extracted_data.json or .md - at a
    usage site a problem ref just collapses to {}, indistinguishable from
    an intentionally empty schema, and neither output file carries a
    warnings/summary section any more. This structure is extraction's own
    record of what got flagged, meant for the Part 3 validation agent to
    consume and fold into validation_report.md - not for either of this
    part's own deliverables."""
    print(f"  Reading {swagger_path}...")
    raw_spec = json.loads(swagger_path.read_text(encoding="utf-8"))
    base_url = swagger_path.resolve().as_uri()

    print("  Checking $ref resolvability (internal + external files/URLs)...")
    ref_status, fetch_cache = compute_ref_status(raw_spec, base_url)

    print("  Resolving $refs (prance)...")
    resolved_spec, broken_occurrences = resolve_with_prance(raw_spec, base_url, ref_status, fetch_cache)
    if on_prance_resolved:
        on_prance_resolved(resolved_spec)
    broken_refs: list[dict[str, str]] = [
        {"type": "unresolvable", "path": path, "ref": ref} for ref, path in broken_occurrences
    ]

    # Two different external refs (or an external ref and an internal
    # schema) can legitimately resolve to the same trailing name; the
    # loser of that naming conflict can't safely collapse to a bare name
    # at its usage sites without silently pointing at the wrong schema.
    external_winners, naming_conflicts = resolve_external_schema_placements(raw_spec, ref_status)
    broken_refs.extend(
        {"type": "naming_conflict", "path": path, "ref": ref, "reason": naming_conflicts[ref]}
        for ref, path in find_refs_in(raw_spec)
        if ref in naming_conflicts
    )

    print("  Extracting metadata and security...")
    metadata = _extract_metadata(raw_spec)
    security = _extract_security(raw_spec)

    print("  Extracting schemas...")
    schemas = extract_schemas(
        raw_spec, resolved_spec, broken_refs, ref_status, naming_conflicts, external_winners, base_url, fetch_cache
    )

    print("  Extracting endpoints...")
    endpoints = extract_endpoints(raw_spec, resolved_spec, broken_refs, ref_status, naming_conflicts)

    print("  Reading user stories...")
    user_stories = userstories_path.read_text(encoding="utf-8") if userstories_path else None

    data = {
        "metadata": metadata,
        "security": security,
        "endpoints": endpoints,
        "schemas": schemas,
        "user_stories": user_stories,
    }
    return data, raw_spec, ref_status, broken_refs


# generate_markdown(data) from .md_generation turns the extracted_data dict
# from run_extraction() above into a human-readable Markdown mirror - also
# pure/deterministic, no I/O. Kept imported here for convenience since it's
# the natural pairing with run_extraction's output; call it directly if a
# Markdown artifact is wanted alongside the dict.
