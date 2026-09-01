"""Interactive entry point: pick a project folder from
project-data-S3/inputs/, then run Part 1 - Hard Gates against its
swagger.json.

Usage:
    python run_ingestion.py
"""

from __future__ import annotations

from pathlib import Path

from ingestion_service.hard_gates import format_report, run_hard_gates
from ingestion_service.project_picker import prompt_for_project

INPUTS_DIR = Path("project-data-S3") / "inputs"


def main() -> int:
    project = prompt_for_project(INPUTS_DIR)
    if project is None:
        return 1

    print(f"\nRunning Hard Gates on: {project.swagger_path}\n")
    result = run_hard_gates(project.swagger_path)
    print(format_report(result))
    return 0 if result.overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
