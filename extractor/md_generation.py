"""Generates extracted_data.md - a human-readable mirror of
extracted_data.json's six sections, plus a broken-$ref summary appended at
the very end with a count of affected endpoints (an endpoint counts as
affected if it directly holds a broken ref, or transitively uses a named
schema whose own body contains one).
"""

from __future__ import annotations

import json
from typing import Any

from .endpoint_extraction import HTTP_METHODS
from .ref_resolution import (
    broken_refs_reachable_from_schema,
    direct_broken_refs,
    direct_schema_names_used,
)


def _compute_affected_endpoints(raw_spec: dict[str, Any], broken_refs: list[str]) -> list[str]:
    broken_set = set(broken_refs)
    affected: list[str] = []

    for path, path_item in raw_spec.get("paths", {}).items():
        if not isinstance(path_item, dict):
            continue
        shared_params = path_item.get("parameters", [])

        for method in HTTP_METHODS:
            operation = path_item.get(method)
            if not isinstance(operation, dict):
                continue

            subtree = {
                "parameters": shared_params + operation.get("parameters", []),
                "requestBody": operation.get("requestBody"),
                "responses": operation.get("responses", {}),
            }

            found = direct_broken_refs(subtree, raw_spec)
            for name in direct_schema_names_used(subtree):
                found |= broken_refs_reachable_from_schema(name, raw_spec, broken_set)

            if found:
                affected.append(f"{method.upper()} {path}")

    return affected


def _section(title: str) -> list[str]:
    return [f"## {title}", ""]


def generate_markdown(data: dict[str, Any], raw_spec: dict[str, Any]) -> str:
    lines: list[str] = ["# Extracted API Data", ""]

    meta = data["metadata"]
    lines += _section("Metadata")
    lines.append(f"- Title: {json.dumps(meta.get('title'))}")
    lines.append(f"- Version: {json.dumps(meta.get('version'))}")
    lines.append(f"- Description: {json.dumps(meta.get('description'))}")
    lines.append(f"- Contact: {json.dumps(meta.get('contact'))}")
    lines.append(f"- License: {json.dumps(meta.get('license'))}")
    lines.append(f"- Servers: {json.dumps(meta.get('servers'))}")
    lines.append(f"- Tags: {json.dumps(meta.get('tags'))}")
    lines.append("")

    lines += _section("Security")
    lines.append(f"- Global requirements: {json.dumps(data['security'].get('global_requirements'))}")
    lines.append("- Schemes:")
    schemes = data["security"].get("schemes", {})
    if schemes:
        for name, scheme in schemes.items():
            lines.append(f"  - {name}: {json.dumps(scheme)}")
    else:
        lines.append("  - none")
    lines.append("")

    lines += _section("Endpoints")
    for entry in data["endpoints"]:
        lines.append(f"### {entry['method']} {entry['path']}")
        lines.append(f"- operationId: {json.dumps(entry.get('operationId'))}")
        lines.append(f"- summary: {json.dumps(entry.get('summary'))}")
        lines.append(f"- description: {json.dumps(entry.get('description'))}")
        lines.append(f"- tags: {json.dumps(entry.get('tags'))}")
        lines.append(f"- security: {json.dumps(entry.get('security'))}")
        lines.append(f"- parameters: {json.dumps(entry.get('parameters'))}")
        lines.append(f"- request_body: {json.dumps(entry.get('request_body'))}")
        lines.append(f"- responses: {json.dumps(entry.get('responses'))}")
        lines.append("")

    lines += _section("Schemas")
    for name, schema in data["schemas"].items():
        lines.append(f"### {name}")
        lines.append("```json")
        lines.append(json.dumps(schema, indent=2))
        lines.append("```")
        lines.append("")

    lines += _section("User Stories")
    lines.append(data["user_stories"] if data["user_stories"] else "(none provided)")
    lines.append("")

    lines += _section("Warnings")
    if data["warnings"]:
        lines += [f"- {w}" for w in data["warnings"]]
    else:
        lines.append("- none")
    lines.append("")

    broken_refs = [w.split(" -> ", 1)[1] for w in data["warnings"] if w.startswith("Unresolvable $ref:")]
    affected_endpoints = _compute_affected_endpoints(raw_spec, broken_refs)
    lines += _section("Broken $ref Summary")
    lines.append(f"- Total broken $ref occurrences: {len(broken_refs)}")
    lines.append(f"- Affected endpoints: {len(affected_endpoints)}")
    for label in affected_endpoints:
        lines.append(f"  - {label}")

    return "\n".join(lines)
