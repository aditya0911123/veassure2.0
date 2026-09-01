"""Interactive picker for selecting a project folder under
project-data-S3/inputs/. Each project folder is expected to contain a
mandatory swagger.json and an optional userstories.txt.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SWAGGER_FILENAME = "swagger.json"
USERSTORIES_FILENAME = "userstories.txt"


@dataclass
class ProjectPaths:
    name: str
    folder: Path
    swagger_path: Path
    userstories_path: Path | None


def list_project_folders(inputs_dir: Path) -> list[Path]:
    if not inputs_dir.is_dir():
        return []
    return sorted(
        (p for p in inputs_dir.iterdir() if p.is_dir()),
        key=lambda p: p.name.lower(),
    )


def resolve_project(folder: Path) -> ProjectPaths:
    swagger_path = folder / SWAGGER_FILENAME
    userstories_path = folder / USERSTORIES_FILENAME
    return ProjectPaths(
        name=folder.name,
        folder=folder,
        swagger_path=swagger_path,
        userstories_path=userstories_path if userstories_path.is_file() else None,
    )


def prompt_for_project(inputs_dir: Path) -> ProjectPaths | None:
    """Print the numbered list of project folders and prompt the user to
    choose one via terminal input. Returns None if there is nothing to pick
    from or the user quits."""
    folders = list_project_folders(inputs_dir)
    if not folders:
        print(f"No project folders found under {inputs_dir}")
        return None

    print("Available projects:")
    for i, folder in enumerate(folders, start=1):
        project = resolve_project(folder)
        story_note = "with user stories" if project.userstories_path else "no user stories"
        print(f"  {i}. {folder.name} ({story_note})")

    while True:
        choice = input(f"Select a project [1-{len(folders)}] (or 'q' to quit): ").strip()
        if choice.lower() in {"q", "quit"}:
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(folders):
            return resolve_project(folders[int(choice) - 1])
        print("Invalid selection, try again.")
