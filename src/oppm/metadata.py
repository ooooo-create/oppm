import json
from pathlib import Path
from typing import TypedDict

from .exceptions import MetaFileError


class AppEntry(TypedDict):
    name: str
    relative_path: str


class Metadata(TypedDict):
    apps: list[AppEntry]


def save_metadata(meta_file: Path, meta: Metadata):
    try:
        meta_file.parent.mkdir(parents=True, exist_ok=True)
        with meta_file.open("w", encoding="utf-8") as f:
            json.dump(meta, f, indent=4, ensure_ascii=False)
    except OSError as e:
        raise MetaFileError(f"Failed to write to metadata file: {e}") from e


def load_metadata(meta_file: Path) -> Metadata:
    if not meta_file.exists():
        raise MetaFileError(f"Metadata file does not exist: {meta_file}")
    try:
        with meta_file.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        raise MetaFileError(f"Failed to read or parse metadata file: {e}") from e


def add_app_to_metadata(app_name: str, app_dir: Path, root_dir: Path, meta_file: Path):
    meta = load_metadata(meta_file)
    try:
        relative_path = app_dir.relative_to(root_dir)
    except ValueError as e:
        raise MetaFileError(f"App directory must be under root directory: {e}") from e
    meta["apps"] = [app for app in meta["apps"] if app["name"] != app_name]
    meta["apps"].append({"name": app_name, "relative_path": relative_path.as_posix()})
    save_metadata(meta_file, meta)


def remove_app_from_metadata(app_name: str, meta_file: Path) -> bool:
    meta = load_metadata(meta_file)
    original_count = len(meta["apps"])
    meta["apps"] = [app for app in meta["apps"] if app["name"] != app_name]
    if len(meta["apps"]) == original_count:
        return False
    save_metadata(meta_file, meta)
    return True
