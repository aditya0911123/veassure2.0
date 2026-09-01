"""CLI entry point for Part 1 - Hard Gates.

Usage:
    python run_hard_gates.py [path-to-swagger.json]

Defaults to project-data-S3/inputs/swagger.json. Terminal output only -
nothing is written to disk.
"""

from __future__ import annotations

import sys
from pathlib import Path

from ingestion_service.hard_gates import format_report, run_hard_gates

DEFAULT_SWAGGER_PATH = Path("project-data-S3") / "inputs" / "swagger.json"


def main() -> int:
    swagger_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SWAGGER_PATH
    result = run_hard_gates(swagger_path)
    print(format_report(result))
    return 0 if result.overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
