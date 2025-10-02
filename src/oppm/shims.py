from pathlib import Path

from .exceptions import ShimError
from .output import error, step, success


def remove_shims_for_app(app_dir: Path, shims_dir: Path) -> None:
    if not shims_dir.exists():
        return

    step("Removing shims...")
    app_dir_resolved = app_dir.resolve()
    for shim_path in shims_dir.iterdir():
        if not shim_path.is_symlink():
            continue
        try:
            target = shim_path.resolve()
            if target.is_relative_to(app_dir_resolved):
                shim_path.unlink()
                success(f"  Removed shim: {shim_path.name}")
        except (OSError, ValueError) as e:
            error(f"  Error removing shim {shim_path.name}: {e}")


def create_shim(execute_path: Path, shim_name: str, shims_dir: Path) -> None:
    shims_dir.mkdir(parents=True, exist_ok=True)
    shim_path = shims_dir / shim_name

    if shim_path.exists():
        raise ShimError(f"Shim '{shim_name}' already exists at {shim_path}")

    try:
        # [NOTE]: Use relative path for symlink to support migration
        relate_execute_path = execute_path.resolve().relative_to(shim_path.parent, walk_up=True)
        shim_path.symlink_to(relate_execute_path)
        success(f"  Created shim: {shim_path} -> {execute_path}")
    except (OSError, AttributeError) as e:
        raise ShimError(
            f"Failed to create shim for {execute_path}: {e}\n On Windows, you may need to run this as an Administrator or enable Developer Mode."
        ) from e


def list_shims(shims_dir: Path) -> list[tuple[str, Path]]:
    if not shims_dir.exists():
        return []

    shims: list[tuple[str, Path]] = []
    for shim_path in shims_dir.iterdir():
        if shim_path.is_symlink():
            try:
                target = shim_path.resolve()
                shims.append((shim_path.name, target))
            except OSError:
                # Skip broken symlinks
                continue

    return sorted(shims, key=lambda x: x[0])
