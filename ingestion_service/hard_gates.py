"""Part 1 - Hard Gates for the VeAssure Ingestion Service.

Deterministic, terminal-only checks run against swagger.json before anything
else in the pipeline is allowed to proceed. Nothing here writes to disk.

Gate 1 - File Parsing: the file must be valid JSON.
Gate 2 - OpenAPI Version: the 'openapi' field must be 3.0.x or 3.1.x.
Gate 3 - OpenAPI Spec Validation: the document must satisfy the OpenAPI
         schema. Broken/unresolvable $refs are reported as warnings and do
         not fail the gate; any other spec violation is fatal.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from openapi_spec_validator import OpenAPIV30SpecValidator, OpenAPIV31SpecValidator

_VERSION_RE = re.compile(r"^3\.(0|1)\.\d+$")

_VALIDATORS = {
    "3.0": OpenAPIV30SpecValidator,
    "3.1": OpenAPIV31SpecValidator,
}


@dataclass
class GateResult:
    file_parsing_pass: bool = False
    version_pass: bool = False
    spec_validation_pass: bool = False
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    spec: dict[str, Any] | None = None

    @property
    def overall_pass(self) -> bool:
        return self.file_parsing_pass and self.version_pass and self.spec_validation_pass


def gate1_parse_file(path: Path, result: GateResult) -> dict[str, Any] | None:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        result.errors.append(f"File Parsing: file not found at {path}")
        return None
    except OSError as exc:
        result.errors.append(f"File Parsing: could not read file ({exc})")
        return None
    except UnicodeDecodeError as exc:
        result.errors.append(f"File Parsing: file is not valid UTF-8 ({exc})")
        return None

    try:
        spec = json.loads(raw)
    except json.JSONDecodeError as exc:
        result.errors.append(
            f"File Parsing: invalid JSON ({exc.msg} at line {exc.lineno}, column {exc.colno})"
        )
        return None

    if not isinstance(spec, dict):
        result.errors.append("File Parsing: top-level JSON must be an object")
        return None

    result.file_parsing_pass = True
    return spec


def gate2_check_version(spec: dict[str, Any], result: GateResult) -> str | None:
    version = spec.get("openapi")
    if not isinstance(version, str) or not version.strip():
        result.errors.append("OpenAPI Version: missing or non-string 'openapi' field")
        return None

    if not _VERSION_RE.match(version):
        result.errors.append(
            f"OpenAPI Version: unsupported version '{version}' (only 3.0.x and 3.1.x are supported)"
        )
        return None

    result.version_pass = True
    return "3.0" if version.startswith("3.0") else "3.1"


def _ref_resolves(ref: str, spec: dict[str, Any]) -> bool:
    """Resolve a $ref against this same document only. External-file refs
    (anything not starting with '#/') are out of scope for local resolution
    and are treated as unresolvable."""
    if not ref.startswith("#/"):
        return False

    node: Any = spec
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(node, dict) and part in node:
            node = node[part]
        elif isinstance(node, list):
            try:
                node = node[int(part)]
            except (ValueError, IndexError):
                return False
        else:
            return False
    return True


def _walk_refs(node: Any, spec: dict[str, Any], path: str, broken: list[str]) -> None:
    """Walk the raw document tree (never following/expanding a $ref's
    target), recording any $ref whose pointer doesn't resolve. Because refs
    are never expanded, a legitimate recursive schema (ref -> ref cycle)
    cannot cause infinite recursion here."""
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and not _ref_resolves(ref, spec):
            broken.append(f"{path} -> {ref}")
        for key, value in node.items():
            _walk_refs(value, spec, f"{path}.{key}", broken)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            _walk_refs(item, spec, f"{path}[{i}]", broken)


def _find_broken_refs(spec: dict[str, Any]) -> list[str]:
    broken: list[str] = []
    _walk_refs(spec, spec, "$", broken)
    return broken


def _patch_broken_refs(node: Any, broken_targets: set[str]) -> Any:
    """Deep-copy node, replacing any $ref pointing at a broken target with
    an always-valid placeholder schema, so the real spec validator can run
    to completion instead of aborting on the unresolvable pointer."""
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref in broken_targets:
            return {}
        return {k: _patch_broken_refs(v, broken_targets) for k, v in node.items()}
    if isinstance(node, list):
        return [_patch_broken_refs(item, broken_targets) for item in node]
    return node


def gate3_validate_spec(spec: dict[str, Any], version_key: str, result: GateResult) -> None:
    broken_ref_paths = _find_broken_refs(spec)
    for entry in broken_ref_paths:
        result.warnings.append(f"Unresolvable $ref: {entry}")

    if broken_ref_paths:
        broken_targets = {entry.split(" -> ", 1)[1] for entry in broken_ref_paths}
        patched_spec = _patch_broken_refs(spec, broken_targets)
    else:
        patched_spec = spec

    validator_cls = _VALIDATORS[version_key]
    try:
        genuine_errors = list(validator_cls(patched_spec).iter_errors())
    except Exception as exc:  # any validator-internal failure is a fatal Gate 3 error
        result.errors.append(f"OpenAPI Specification Validation: validator error ({exc})")
        return

    if genuine_errors:
        for err in genuine_errors:
            location = "/".join(str(p) for p in err.path) or "(root)"
            result.errors.append(f"OpenAPI Specification Validation: {location}: {err.message}")
        return

    result.spec_validation_pass = True


def run_hard_gates(swagger_path: Path) -> GateResult:
    result = GateResult()

    spec = gate1_parse_file(swagger_path, result)
    if spec is None:
        return result
    result.spec = spec

    version_key = gate2_check_version(spec, result)
    if version_key is None:
        return result

    gate3_validate_spec(spec, version_key, result)
    return result


def format_report(result: GateResult) -> str:
    lines = [
        f"HARD GATE: {'PASS' if result.overall_pass else 'FAIL'}",
        "",
        f"File Parsing: {'PASS' if result.file_parsing_pass else 'FAIL'}",
        f"OpenAPI Version: {'PASS' if result.version_pass else 'FAIL'}",
        f"OpenAPI Specification Validation: {'PASS' if result.spec_validation_pass else 'FAIL'}",
        "",
        "Warnings:",
    ]
    lines += [f"- {w}" for w in result.warnings] if result.warnings else ["- none"]
    lines += ["", "Errors:"]
    lines += [f"- {e}" for e in result.errors] if result.errors else ["- none"]
    return "\n".join(lines)
