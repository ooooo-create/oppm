import sys
from pathlib import Path
from typing import Annotated

import typer

from . import commands
from .config import load_config
from .exceptions import OPPMError

DEFAULT_ROOT_DIR = Path.home() / ".oppm"

app = typer.Typer(
    name="oppm",
    help="A lightweight portable application manager",
    add_completion=True,
    rich_markup_mode="rich",
)

exe_app = typer.Typer(help="Manage executable shims")
app.add_typer(exe_app, name="exe")


@app.command()
def init(
    root_dir: Annotated[
        Path,
        typer.Option("-r", "--root-dir", help="Root directory for OPPM"),
    ] = DEFAULT_ROOT_DIR,
):
    """Initialize OPPM directories and configuration"""
    try:
        root_dir.mkdir(parents=True, exist_ok=True)
        commands.initialize(root_dir)
    except OPPMError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e


@app.command()
def list():
    """List all installed applications"""
    try:
        config = load_config()
        commands.list_apps(config)
    except OPPMError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e


@app.command()
def install(
    input_path: Annotated[Path, typer.Argument(help="Path to the application to install")],
    name: Annotated[str | None, typer.Option("-n", "--name", help="Custom name for the application")] = None,
):
    """Install an application"""
    try:
        config = load_config()
        commands.install_app(input_path, config, name)
    except OPPMError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e


@app.command()
def remove(
    app_name: Annotated[str, typer.Argument(help="Name of the application to remove")],
):
    """Remove an application"""
    try:
        config = load_config()
        commands.remove_app(app_name, config)
    except OPPMError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e


@app.command()
def update():
    """Synchronize metadata with installed applications"""
    try:
        config = load_config()
        commands.update_metadata(config)
    except OPPMError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e


@app.command()
def clean():
    """Remove all applications and clean directories"""
    try:
        config = load_config()
        commands.clean_all(config)
    except OPPMError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e


@app.command()
def migrate(
    new_root_dir: Annotated[Path, typer.Argument(help="New root directory for OPPM")],
):
    """Migrate OPPM to a new root directory"""
    try:
        config = load_config()
        commands.migrate_root(config.root_dir, new_root_dir.resolve())
    except OPPMError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e


@app.command()
def pack(
    output: Annotated[
        Path | None,
        typer.Option("-o", "--output", help="Output archive path (default: oppm_backup_YYYYMMDD_HHMMSS.tar.gz)"),
    ] = None,
    overwrite: Annotated[bool, typer.Option("--overwrite", help="Overwrite existing archive")] = False,
):
    """Pack the entire OPPM root directory into an archive"""
    try:
        config = load_config()
        commands.pack(config, output, overwrite)
    except OPPMError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e


@app.command()
def rebuild(
    archive: Annotated[Path, typer.Argument(help="Archive file to rebuild from")],
    root_dir: Annotated[
        Path,
        typer.Option("-r", "--root-dir", help="Target root directory"),
    ] = DEFAULT_ROOT_DIR,
):
    """Rebuild OPPM structure from a packed archive"""
    try:
        commands.rebuild(archive, root_dir)
    except OPPMError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e


# [TODO]
# @app.command()
# def verify(
#     fix: Annotated[bool, typer.Option("--fix", help="Automatically fix issues")] = False,
# ):
#     try:
#         config = load_config()
#         is_valid = commands.verify_metadata(config, fix)
#         if not is_valid and not fix:
#             raise typer.Exit(code=1)
#     except OPPMError as e:
#         typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
#         raise typer.Exit(code=1) from e


@exe_app.command("add")
def exe_add(
    exe_path: Annotated[Path, typer.Argument(help="Path to the executable")],
    name: Annotated[str | None, typer.Option("-n", "--name", help="Custom name for the shim")] = None,
):
    """Add a shim for an executable"""
    try:
        config = load_config()
        commands.add_executable(exe_path, name, config)
    except OPPMError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e


@exe_app.command("delete")
def exe_delete(
    shim_name: Annotated[str, typer.Argument(help="Name of the shim to delete")],
):
    """Delete an executable shim"""
    try:
        config = load_config()
        commands.delete_executable(shim_name, config)
    except OPPMError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e


@exe_app.command("show")
def exe_show():
    """Show all executable shims"""
    try:
        config = load_config()
        commands.show_shims(config)
    except OPPMError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e


@app.command()
def config():
    """Show current configuration"""
    try:
        config_obj = load_config()
        commands.show_config(config_obj)
    except OPPMError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e


def main() -> None:
    """Main entry point for the CLI."""
    try:
        app()
    except KeyboardInterrupt:
        typer.secho("\nOperation cancelled by user.", fg=typer.colors.YELLOW, err=True)
        sys.exit(130)
    except Exception as e:
        if not isinstance(e, (typer.Exit, OPPMError)):
            typer.secho(f"Unexpected error: {e}", fg=typer.colors.RED, err=True)
            sys.exit(1)


if __name__ == "__main__":
    main()
