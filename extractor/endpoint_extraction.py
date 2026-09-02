"""Builds the 'endpoints' section of extracted_data.json from paths. Each
entry keeps its parameters/requestBody/responses structure, with any $ref
to a named schema collapsed to that schema's bare name via
build_clean_view rather than expanded inline - so the schema identity
stays intact for downstream consumers instead of dissolving into an
anonymous object.
"""

from __future__ import annotations

from typing import Any

from .ref_resolution import build_clean_view

HTTP_METHODS = ("get", "put", "post", "delete", "options", "head", "patch", "trace")


def extract_endpoints(
    raw_spec: dict[str, Any], resolved_spec: dict[str, Any], warnings: list[str]
) -> list[dict[str, Any]]:
    endpoints: list[dict[str, Any]] = []
    raw_paths = raw_spec.get("paths", {})
    resolved_paths = resolved_spec.get("paths", {})

    for path, raw_path_item in raw_paths.items():
        if not isinstance(raw_path_item, dict):
            continue
        resolved_path_item = resolved_paths.get(path, {})
        if not isinstance(resolved_path_item, dict):
            resolved_path_item = {}

        raw_shared_params = raw_path_item.get("parameters", [])
        resolved_shared_params = resolved_path_item.get("parameters", [])

        for method in HTTP_METHODS:
            raw_operation = raw_path_item.get(method)
            if not isinstance(raw_operation, dict):
                continue
            resolved_operation = resolved_path_item.get(method, {})
            if not isinstance(resolved_operation, dict):
                resolved_operation = {}

            base_path = f"paths.{path}.{method}"

            raw_parameters = raw_shared_params + raw_operation.get("parameters", [])
            resolved_parameters = resolved_shared_params + resolved_operation.get("parameters", [])

            entry = {
                "path": path,
                "method": method.upper(),
                "operationId": raw_operation.get("operationId"),
                "summary": raw_operation.get("summary"),
                "description": raw_operation.get("description"),
                "tags": raw_operation.get("tags", []),
                "security": raw_operation.get("security"),
                "parameters": build_clean_view(
                    raw_parameters, resolved_parameters, raw_spec, f"{base_path}.parameters", warnings
                ),
                "request_body": build_clean_view(
                    raw_operation.get("requestBody"),
                    resolved_operation.get("requestBody"),
                    raw_spec,
                    f"{base_path}.requestBody",
                    warnings,
                ),
                "responses": build_clean_view(
                    raw_operation.get("responses", {}),
                    resolved_operation.get("responses", {}),
                    raw_spec,
                    f"{base_path}.responses",
                    warnings,
                ),
            }
            endpoints.append(entry)

    return endpoints
