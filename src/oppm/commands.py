import platform
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from .config import OPPMConfig, save_config, update_config
from .exceptions import AppNotFoundError, InstallError, InvalidInputError, MigrationError, PackError, RebuildError
from .metadata import add_app_to_metadata, load_metadata, remove_app_from_metadata, save_metadata
from .output import console, create_table, error, info, step, success, warning
from .shims import create_shim, list_shims, remove_shims_for_app

EXE_TYPES = {".exe", ".bat", ".cmd"}
UNARY_ARCHIVE_TYPES = {".zip", ".tar", ".tgz", ".tbz2", ".txz"}
BINARY_ARCHIVE_TYPES = {".tar.gz", ".tar.bz2", ".tar.xz"}


def _extract_app_name_from_path(input_path: Path) -> str:
    if input_path.is_dir():
        return input_path.name
    elif input_path.is_file():
        if input_path.suffix in EXE_TYPES | UNARY_ARCHIVE_TYPES:
            return input_path.stem
        elif any(str(input_path).endswith(s) for s in BINARY_ARCHIVE_TYPES):
            return Path(input_path.stem).stem
        else:
            raise InvalidInputError(
                f"Unsupported file type: {input_path.suffix}. Supported types: .exe, {', '.join(EXE_TYPES | UNARY_ARCHIVE_TYPES | BINARY_ARCHIVE_TYPES)}"
            )
    else:
        raise InvalidInputError(f"Input path does not exist or is not a file/directory: {input_path}")


def _print_shims_to_path_instructions(shims_dir: Path) -> None:
    warning("\n--- IMPORTANT NEXT STEP ---")
    info("To complete the setup, you need to add the shims directory to your system's PATH.")
    info(
        "Please add the following line to your shell's configuration file (e.g., .zshrc, .bashrc, or PowerShell profile):\n"
    )
    current_os = platform.system()
    if current_os == "Windows":
        console.print(f'  [cyan]$env:PATH += ";{shims_dir.resolve()}"[/cyan]')
        info("\nThen, restart your terminal for the changes to take effect.")
    elif current_os in ["Linux", "Darwin"]:
        console.print(f'  [cyan]export PATH="{shims_dir.resolve()}:$PATH"[/cyan]')
        info("\nThen, run 'source ~/.your_shell_rc_file' or restart your terminal.")
    else:
        warning(f"Your OS ({current_os}) is not automatically detected. Please add this path to your PATH manually:")
        info(f"  {shims_dir.resolve()}")


def _extract_and_place_archive(archive_path: Path, target_dir: Path) -> None:
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        step("📦 Extracting archive to temporary location...")

        shutil.unpack_archive(archive_path, temp_dir, filter="data")

        # Archive should contain a single root directory
        extracted_items = list(temp_dir.iterdir())
        if len(extracted_items) != 1 or not extracted_items[0].is_dir():
            raise RebuildError("Archive is invalid: it must contain a single root directory (e.g., '.oppm').")
        extracted_root = extracted_items[0]

        # Safely move to final target location
        if target_dir.exists():
            shutil.rmtree(target_dir)

        _ = shutil.move(str(extracted_root), str(target_dir))
        success(f"✅ Extracted to: {target_dir}")


def initialize(root_dir: Path) -> None:
    apps_dir = root_dir / "apps"
    meta_file = root_dir / "meta.json"
    shims_dir = root_dir / "shims"

    root_dir.mkdir(parents=True, exist_ok=True)
    apps_dir.mkdir(exist_ok=True)
    shims_dir.mkdir(exist_ok=True)

    if not meta_file.exists():
        step("Creating meta.json ...")
        save_metadata(meta_file, {"apps": []})

    config = OPPMConfig(root_dir=root_dir, apps_dir=apps_dir, meta_file=meta_file, shims_dir=shims_dir)
    save_config(config)
    _print_shims_to_path_instructions(shims_dir)


def list_apps(config: OPPMConfig) -> None:
    meta = load_metadata(config.meta_file)
    if not meta["apps"]:
        warning("No applications installed.")
        return
    table = create_table("📦 Installed Applications", "Name", "Path")
    for app in sorted(meta["apps"], key=lambda x: x["name"]):
        app_path = config.root_dir / app["relative_path"]
        table.add_row(app["name"], str(app_path))
    console.print(table)


def install_app(input_path: Path, config: OPPMConfig, name: str | None = None) -> None:
    if not input_path.exists():
        raise InvalidInputError(f"Input file or directory does not exist: {input_path}")
    app_name = _extract_app_name_from_path(input_path)
    if name:
        app_name = name
    app_dir = config.apps_dir / app_name
    if app_dir.exists():
        warning(f"Application '{app_name}' already exists. Removing old version...")
        shutil.rmtree(app_dir)
    try:
        step("Installing application...")
        if input_path.is_dir():
            _ = shutil.copytree(input_path, app_dir)
        elif input_path.is_file():
            app_dir.mkdir(parents=True, exist_ok=True)
            if input_path.suffix in EXE_TYPES:
                _ = shutil.copy(input_path, app_dir)
            else:
                # It's an archive file (validated in extract_app_name)
                shutil.unpack_archive(input_path, app_dir)
        else:
            raise InvalidInputError(f"Unsupported file type: {input_path}")
    except InvalidInputError:
        raise
    except Exception as e:
        # Clean up on failure
        if app_dir.exists():
            shutil.rmtree(app_dir)
        raise InstallError(f"Failed to install '{app_name}': {e}") from e

    add_app_to_metadata(app_name, app_dir, config.root_dir, config.meta_file)
    success(f"Successfully installed {app_name}")


def remove_app(app_name: str, config: OPPMConfig) -> None:
    removed = remove_app_from_metadata(app_name, config.meta_file)
    if not removed:
        raise AppNotFoundError(
            f"Application '{app_name}' not found in metadata. Maybe you can call 'oppm update' to update the metadata first."
        )
    app_dir = config.apps_dir / app_name
    remove_shims_for_app(app_dir, config.shims_dir)
    if app_dir.exists():
        shutil.rmtree(app_dir)
        step(f"Successfully removed application directory: {app_dir}")
    else:
        warning(f"Application directory '{app_dir}' does not exist, may have been manually deleted.")
    success(f"Successfully removed {app_name}")


def update_metadata(config: OPPMConfig) -> None:
    if not config.apps_dir.exists():
        error("Application directory does not exist, cannot update.")
        return
    try:
        actual_apps = {app.name for app in config.apps_dir.iterdir() if app.is_dir()}
        meta = load_metadata(config.meta_file)
        meta_apps = {app["name"] for app in meta["apps"]}
    except FileNotFoundError:
        error("Metadata file does not exist, cannot update.")
        return

    apps_to_add = actual_apps - meta_apps
    apps_to_remove = meta_apps - actual_apps

    if apps_to_add:
        info(f"Found {len(apps_to_add)} apps to add: {apps_to_add}")
        for app_name in apps_to_add:
            app_dir = config.apps_dir / app_name
            relative_path = app_dir.relative_to(config.root_dir)
            meta["apps"].append({"name": app_name, "relative_path": relative_path.as_posix()})
    if apps_to_remove:
        info(f"Found {len(apps_to_remove)} apps to remove: {apps_to_remove}")
        meta["apps"] = [app for app in meta["apps"] if app["name"] not in apps_to_remove]

    if not apps_to_add and not apps_to_remove:
        info("No changes found.")
        return
    save_metadata(config.meta_file, meta)
    success("Update complete")


def clean_all(config: OPPMConfig) -> None:
    if config.apps_dir.exists():
        for item in config.apps_dir.iterdir():
            step(f"Removing {item.name} ...")
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    if config.shims_dir.exists():
        for shim in config.shims_dir.iterdir():
            if shim.is_symlink():
                step(f"Removing shim {shim.name} ...")
                shim.unlink()
    save_metadata(config.meta_file, {"apps": []})
    success("Cleaning complete")


def migrate_root(old_root_dir: Path, new_root_dir: Path) -> None:
    if not old_root_dir.exists():
        raise MigrationError(f"Old root directory does not exist: {old_root_dir}")

    old_root_resolved = old_root_dir.resolve()
    new_root_resolved = new_root_dir.resolve()

    if old_root_resolved == new_root_resolved:
        info("Source and destination are the same. Nothing to do.")
        return

    if new_root_dir.exists():
        if any(new_root_dir.iterdir()):
            raise MigrationError(f"Target directory '{new_root_dir}' exists and is not empty. Please remove it first.")
        shutil.rmtree(new_root_dir)

    step(f"Migrating from '{old_root_dir}' to '{new_root_dir}' ...")

    try:
        _ = shutil.move(str(old_root_dir), str(new_root_dir))
    except Exception as e:
        raise MigrationError(f"Failed to move directory: {e}") from e
    success("✅ Metadata paths are relative, no update needed.")
    new_meta_file = new_root_dir / "meta.json"
    new_apps_dir = new_root_dir / "apps"
    new_shims_dir = new_root_dir / "shims"

    new_config = OPPMConfig(
        root_dir=new_root_dir, apps_dir=new_apps_dir, meta_file=new_meta_file, shims_dir=new_shims_dir
    )
    update_config(new_config)
    step("Updated configuration file")
    success("Migration complete!")
    _print_shims_to_path_instructions(new_shims_dir)


def pack(config: OPPMConfig, output_path: Path | None = None, overwrite: bool = False) -> None:
    root_dir = config.root_dir.resolve()
    if not root_dir.exists() or not root_dir.is_dir():
        raise PackError(f"Root directory does not exist or is not a directory: {root_dir}")

    if output_path is None:
        timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path.cwd() / "oppm_backups"
        backup_dir.mkdir(exist_ok=True)
        output_file = backup_dir / f"oppm_backup_{timestamp}.tar.gz"
    else:
        output_file = output_path.resolve()
        output_file.parent.mkdir(parents=True, exist_ok=True)
        if not str(output_file).endswith(".tar.gz"):
            output_file = output_file.with_suffix(".tar.gz")
    if output_file.exists() and not overwrite:
        raise PackError(
            f"Output file already exists: {output_file}\nUse the '--overwrite' flag if you want to replace it."
        )
    step("📦 Starting to pack OPPM directory...")
    info(f"   Source: {root_dir}")
    info(f"   Destination: {output_file}")
    try:
        base_name = str(output_file.with_suffix("").with_suffix(""))
        archive_path_str = shutil.make_archive(
            base_name=base_name, format="gztar", root_dir=root_dir.parent, base_dir=root_dir.name
        )
        final_archive_path = Path(archive_path_str)
        if final_archive_path != output_file:
            raise PackError(
                f"Unexpected error: packed file '{final_archive_path}' does not match expected output '{output_file}'."
            )
        archive_size_mb = output_file.stat().st_size / (1024 * 1024)
        success("\n🎉 Packing complete!")
        info(f"   Archive: {output_file}")
        info(f"   Size: {archive_size_mb:.2f} MB")
        info("\n💡 Use 'oppm rebuild' to restore this backup.")
    except Exception as e:
        # Cleanup incomplete file on failure
        if output_file.exists():
            try:
                output_file.unlink()
            except OSError:
                raise PackError(f"Failed to create archive: {e}") from e


def rebuild(archive_path: Path, new_root_dir: Path | None = None) -> None:
    if not archive_path.exists():
        raise InvalidInputError(f"Archive not found: {archive_path}")
    if not str(archive_path).endswith(".tar.gz"):
        raise InvalidInputError(f"Unsupported archive format: {archive_path.name}. Must be .tar.gz")
    target_dir = new_root_dir
    if target_dir is None:
        try:
            from .config import load_config

            target_dir = load_config().root_dir
            info(f"📁 Using existing root directory for rebuild: {target_dir}")
        except Exception as e:
            raise InvalidInputError(
                "Rebuild target directory not specified and no config found.\nPlease specify a target with '-r <path>' or run 'oppm init' first."
            ) from e
    target_dir = target_dir.resolve()
    if target_dir.exists() and any(target_dir.iterdir()):
        response = input(f"⚠️  Directory '{target_dir}' is not empty. Overwrite? (y/n): ")
        if response.lower() != "y":
            warning("Rebuild cancelled.")
            return
    try:
        _extract_and_place_archive(archive_path, target_dir)
        meta_file = target_dir / "meta.json"
        apps_dir = target_dir / "apps"
        shims_dir = target_dir / "shims"
        step("⚙️  Updating main configuration file...")
        new_config = OPPMConfig(
            root_dir=target_dir,
            apps_dir=apps_dir,
            meta_file=meta_file,
            shims_dir=shims_dir,
        )
        save_config(new_config)
        success("✅ Configuration saved.")
        success("\n🎉 Rebuild complete!")
        info(f"   Root is now: {target_dir}")
        _print_shims_to_path_instructions(shims_dir)
    except Exception as e:
        raise RebuildError(f"Failed during rebuild process: {e}") from e


def add_executable(exe_path: Path, exe_name: str | None, config: OPPMConfig) -> None:
    if not exe_path.exists():
        raise InvalidInputError(f"Executable not found: {exe_path}")

    shim_name = exe_name if exe_name else exe_path.name

    step("Creating shim...")
    if not exe_path.is_relative_to(config.apps_dir):
        raise InvalidInputError(
            f"Executable must be inside the apps directory: {config.apps_dir}, maybe you can call 'oppm install' first?"
        )
    create_shim(exe_path, shim_name, config.shims_dir)
    success(f"Successfully added {shim_name}")


def delete_executable(shim_name: str, config: OPPMConfig) -> None:
    shim_path = config.shims_dir / shim_name

    if not shim_path.exists():
        raise InvalidInputError(f"Shim not found: {shim_name}")

    if not shim_path.is_symlink():
        raise InvalidInputError(f"{shim_name} is not a shim (not a symlink)")

    # Remove the shim
    shim_path.unlink()
    success(f"Successfully deleted shim: {shim_name}")


def show_shims(config: OPPMConfig) -> None:
    """Display all shims in the shims directory.

    Args:
        config: OPPM configuration.
    """
    shims = list_shims(config.shims_dir)

    if not shims:
        warning("No shims found.")
        return

    table = create_table("🔗 Installed Shims", "Shim Name", "Target")
    for shim_name, target in shims:
        table.add_row(shim_name, str(target))

    console.print(table)


def show_config(config: OPPMConfig) -> None:
    from .config import CONFIG_FILE

    info("Current OPPM Configuration:")
    info(f"  - Root Directory: {config.root_dir}")
    info(f"  - Applications Directory: {config.apps_dir}")
    info(f"  - Metadata File: {config.meta_file}")
    info(f"  - Shims Directory: {config.shims_dir}")
    info(f"\nConfiguration file location: {CONFIG_FILE}")
