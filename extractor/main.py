"""Part 2 entry point: pick a project, run Hard Gates, then extract
deterministic data from swagger.json (+ optional userstories.txt) into
project-data-S3/outputs/<project-name>/extracted_data.json and .md - one
subfolder per project, so re-running extraction for one project never
overwrites another's output.

Usage:
    python -m extractor.main
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ingestion_service.hard_gates import format_report, run_hard_gates
from ingestion_service.project_picker import prompt_for_project

from .endpoint_extraction import extract_endpoints
from .md_generation import generate_markdown
from .ref_resolution import resolve_with_prance
from .schema_extraction import extract_schemas

INPUTS_DIR = Path("project-data-S3") / "inputs"
OUTPUTS_DIR = Path("project-data-S3") / "outputs"


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
    swagger_path: Path, userstories_path: Path | None
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Pure extraction: reads the two input files and returns
    (extracted_data, raw_spec). No interactive I/O beyond progress prints -
    safe to call from a future orchestrator."""
    print(f"  Reading {swagger_path}...")
    raw_spec = json.loads(swagger_path.read_text(encoding="utf-8"))

    print("  Resolving $refs (prance)...")
    resolved_spec, broken_occurrences = resolve_with_prance(raw_spec)
    warnings: list[str] = [f"Unresolvable $ref: {path} -> {ref}" for ref, path in broken_occurrences]

    print("  Extracting metadata and security...")
    metadata = _extract_metadata(raw_spec)
    security = _extract_security(raw_spec)

    print("  Extracting schemas...")
    schemas = extract_schemas(raw_spec, resolved_spec, warnings)

    print("  Extracting endpoints...")
    endpoints = extract_endpoints(raw_spec, resolved_spec, warnings)

    print("  Reading user stories...")
    user_stories = userstories_path.read_text(encoding="utf-8") if userstories_path else None

    data = {
        "metadata": metadata,
        "security": security,
        "endpoints": endpoints,
        "schemas": schemas,
        "user_stories": user_stories,
        "warnings": warnings,
    }
    return data, raw_spec


def main() -> int:
    print("Step 1/4: Selecting project...")
    project = prompt_for_project(INPUTS_DIR)
    if project is None:
        return 1

    print(f"\nStep 2/4: Running Hard Gates on {project.swagger_path}...")
    gate_result = run_hard_gates(project.swagger_path)
    print(format_report(gate_result))
    if not gate_result.overall_pass:
        print("\nHard Gates failed - stopping before extraction.")
        return 1

    print("\nStep 3/4: Extracting data...")
    data, raw_spec = run_extraction(project.swagger_path, project.userstories_path)

    print("\nStep 4/4: Writing output files...")
    project_outputs_dir = OUTPUTS_DIR / project.name
    project_outputs_dir.mkdir(parents=True, exist_ok=True)

    json_path = project_outputs_dir / "extracted_data.json"
    json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"  Wrote {json_path}")

    md_path = project_outputs_dir / "extracted_data.md"
    md_path.write_text(generate_markdown(data, raw_spec), encoding="utf-8")
    print(f"  Wrote {md_path}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
