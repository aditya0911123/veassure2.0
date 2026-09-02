"""Generates extracted_data.md - a human-readable mirror of
extracted_data.json's six sections, plus a broken-$ref summary appended at
the very end with a count of affected endpoints (an endpoint counts as
affected if it directly holds a broken ref, or transitively uses a named
schema whose own body contains one).

Schemas and endpoints are rendered as readable markdown (headings/bullets),
never as raw JSON dumps. A "schema slot" - any position that could hold a
schema reference (a property value, array items, an allOf/oneOf/anyOf
member, a parameter's schema, a response/request body schema) - is one of
three things coming out of build_clean_view, and every renderer below
switches on exactly these three shapes:
  - a bare string  -> a resolved reference; rendered as `Name`
  - {"$ref": ..., "unresolvable": true} -> a broken reference; rendered as
    the inline warning glyph
  - a plain dict with no "$ref" -> an inline schema, rendered in full
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

_CONSTRAINT_KEYS = (
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "minLength",
    "maxLength",
    "pattern",
    "minItems",
    "maxItems",
    "uniqueItems",
    "minProperties",
    "maxProperties",
    "multipleOf",
)


def _ref_label(value: Any) -> str | None:
    """If value is a schema-reference slot (resolved name string, or a
    broken-ref marker), return its inline label. Otherwise None, meaning
    the caller should render it as an inline schema instead.

    Two broken-ref marker shapes exist: build_clean_view's inline
    usage-site marker uses key "$ref", while extract_schemas' top-level
    placeholder for a referenced-but-never-defined schema uses "ref" -
    both are checked here."""
    if isinstance(value, str):
        return f"`{value}`"
    if isinstance(value, dict) and value.get("unresolvable"):
        ref = value.get("$ref") or value.get("ref")
        return f"⚠️ unresolvable $ref → {ref}"
    return None


def _constraints_of(schema: dict[str, Any]) -> list[str]:
    return [f"{k}={json.dumps(schema[k])}" for k in _CONSTRAINT_KEYS if k in schema]


def _type_summary(schema: Any) -> str:
    """Short type description for an inline schema dict: 'string',
    'array of `Comment`', 'object', 'composed schema', etc."""
    ref_label = _ref_label(schema)
    if ref_label:
        return ref_label
    if not isinstance(schema, dict):
        return "unspecified"

    schema_type = schema.get("type")
    if schema_type == "array":
        items = schema.get("items")
        items_label = _ref_label(items)
        if items_label:
            return f"array of {items_label}"
        if isinstance(items, dict):
            return f"array of {_type_summary(items)}"
        return "array"
    if schema_type:
        fmt = schema.get("format")
        return f"{schema_type} ({fmt})" if fmt else schema_type
    if any(k in schema for k in ("allOf", "oneOf", "anyOf")):
        return "composed schema"
    return "object"


def _render_property(name: str, value: Any, required: bool, lines: list[str], indent: str) -> None:
    req_suffix = " *(required)*" if required else ""

    ref_label = _ref_label(value)
    if ref_label:
        lines.append(f"{indent}- **{name}**: {ref_label}{req_suffix}")
        return

    schema = value if isinstance(value, dict) else {}
    lines.append(f"{indent}- **{name}**: {_type_summary(schema)}{req_suffix}")
    _render_schema_details(schema, lines, indent + "  ")


def _render_schema_details(schema: dict[str, Any], lines: list[str], indent: str) -> None:
    """Detail sub-bullets for an inline schema dict: description,
    constraints, enum, default, example. Does not render type/name - the
    caller already put that on the parent bullet line."""
    if schema.get("description"):
        lines.append(f"{indent}- Description: {schema['description']}")

    constraints = _constraints_of(schema)
    if constraints:
        lines.append(f"{indent}- Constraints: {', '.join(constraints)}")

    if "enum" in schema:
        lines.append(f"{indent}- Enum: {', '.join(json.dumps(v) for v in schema['enum'])}")

    if "default" in schema:
        lines.append(f"{indent}- Default: {json.dumps(schema['default'])}")

    example = schema.get("example", schema.get("examples"))
    if example is not None:
        lines.append(f"{indent}- Example: {json.dumps(example)}")


def _render_schema_body(schema: Any, lines: list[str], indent: str = "") -> None:
    """Full rendering of a schema slot - used both for a top-level named
    schema and recursively for nested inline schemas (allOf members,
    array items)."""
    ref_label = _ref_label(schema)
    if ref_label:
        lines.append(f"{indent}- {ref_label}")
        return

    if not isinstance(schema, dict):
        lines.append(f"{indent}- (unrecognized schema value: {json.dumps(schema)})")
        return

    for keyword in ("allOf", "oneOf", "anyOf"):
        members = schema.get(keyword)
        if members is None:
            continue
        lines.append(f"{indent}- Composition: {keyword}")
        for member in members:
            member_label = _ref_label(member)
            if member_label:
                lines.append(f"{indent}  - extends {member_label}")
            else:
                lines.append(f"{indent}  - inline schema:")
                _render_schema_body(member, lines, indent + "    ")
        return

    if schema.get("description"):
        lines.append(f"{indent}- Description: {schema['description']}")

    lines.append(f"{indent}- Type: {_type_summary(schema)}")

    constraints = _constraints_of(schema)
    if constraints:
        lines.append(f"{indent}- Constraints: {', '.join(constraints)}")

    if "enum" in schema:
        lines.append(f"{indent}- Enum: {', '.join(json.dumps(v) for v in schema['enum'])}")

    if "default" in schema:
        lines.append(f"{indent}- Default: {json.dumps(schema['default'])}")

    example = schema.get("example", schema.get("examples"))
    if example is not None:
        lines.append(f"{indent}- Example: {json.dumps(example)}")

    properties = schema.get("properties")
    if properties:
        required = set(schema.get("required", []))
        lines.append(f"{indent}- Properties:")
        for prop_name, prop_value in properties.items():
            _render_property(prop_name, prop_value, prop_name in required, lines, indent + "  ")

    if schema.get("type") == "array":
        items = schema.get("items")
        if isinstance(items, dict) and not items.get("unresolvable"):
            lines.append(f"{indent}- Items:")
            _render_schema_body(items, lines, indent + "  ")


def _render_parameters(parameters: list[dict[str, Any]] | None, lines: list[str], indent: str) -> None:
    if not parameters:
        lines.append(f"{indent}- (none)")
        return

    for param in parameters:
        name = param.get("name")
        location = param.get("in")
        req_label = "required" if param.get("required") else "optional"
        type_desc = _type_summary(param.get("schema"))
        lines.append(f"{indent}- **{name}** ({location}, {req_label}): {type_desc}")
        if param.get("description"):
            lines.append(f"{indent}  - Description: {param['description']}")


def _render_content_schemas(content: dict[str, Any] | None, lines: list[str], indent: str) -> None:
    if not content:
        return
    for media_type, media_obj in content.items():
        schema = media_obj.get("schema") if isinstance(media_obj, dict) else None
        lines.append(f"{indent}- {media_type}: {_type_summary(schema)}")


def _render_request_body(request_body: dict[str, Any] | None, lines: list[str], indent: str) -> None:
    if not request_body:
        lines.append(f"{indent}- (none)")
        return

    req_label = "required" if request_body.get("required") else "optional"
    lines.append(f"{indent}- {req_label}")
    _render_content_schemas(request_body.get("content"), lines, indent + "  ")


def _render_responses(responses: dict[str, Any] | None, lines: list[str], indent: str) -> None:
    if not responses:
        lines.append(f"{indent}- (none)")
        return

    for code, response in responses.items():
        description = response.get("description") if isinstance(response, dict) else None
        lines.append(f"{indent}- **{code}**: {description or '(no description)'}")
        if isinstance(response, dict):
            _render_content_schemas(response.get("content"), lines, indent + "  ")


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

        lines.append("- Parameters:")
        _render_parameters(entry.get("parameters"), lines, "  ")

        lines.append("- Request body:")
        _render_request_body(entry.get("request_body"), lines, "  ")

        lines.append("- Responses:")
        _render_responses(entry.get("responses"), lines, "  ")

        lines.append("")

    lines += _section("Schemas")
    for name, schema in data["schemas"].items():
        lines.append(f"### {name}")
        _render_schema_body(schema, lines)
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
