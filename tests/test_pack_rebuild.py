"""Tests for pack and rebuild commands."""

import json
import shutil
from pathlib import Path

import pytest

from oppm.commands import pack, rebuild
from oppm.config import OPPMConfig
from oppm.exceptions import InvalidInputError, PackError, RebuildError


def test_pack_creates_archive(tmp_path):
    """Test that pack creates a valid tar.gz archive."""
    # Setup: create a mock OPPM directory
    root_dir = tmp_path / ".oppm"
    apps_dir = root_dir / "apps"
    shims_dir = root_dir / "shims"
    meta_file = root_dir / "meta.json"

    apps_dir.mkdir(parents=True)
    shims_dir.mkdir(parents=True)

    # Create a test app
    test_app = apps_dir / "testapp"
    test_app.mkdir()
    (test_app / "app.exe").write_text("fake exe")

    # Create metadata
    meta_file.write_text(json.dumps({"apps": [{"name": "testapp", "path": str(test_app)}]}))

    # Create config
    config = OPPMConfig(root_dir=root_dir, apps_dir=apps_dir, meta_file=meta_file, shims_dir=shims_dir)

    # Test pack
    output_path = tmp_path / "test-backup.tar.gz"
    pack(config, output_path)

    # Verify archive was created
    assert output_path.exists()
    # Check it's a valid archive by trying to list contents
    assert output_path.suffix == ".gz"
    assert output_path.stem.endswith(".tar")


def test_pack_default_filename(tmp_path, monkeypatch):
    """Test that pack generates a timestamped filename by default."""
    # Setup
    root_dir = tmp_path / ".oppm"
    apps_dir = root_dir / "apps"
    meta_file = root_dir / "meta.json"
    shims_dir = root_dir / "shims"
    apps_dir.mkdir(parents=True)
    meta_file.write_text(json.dumps({"apps": []}))

    config = OPPMConfig(root_dir=root_dir, apps_dir=apps_dir, meta_file=meta_file, shims_dir=shims_dir)

    # Change to tmp_path so the default output goes there
    monkeypatch.chdir(tmp_path)

    # Pack without specifying output
    pack(config)

    # Check that a file matching pattern exists in oppm_backups directory
    backup_dir = tmp_path / "oppm_backups"
    assert backup_dir.exists()
    backups = list(backup_dir.glob("oppm_backup_*.tar.gz"))
    assert len(backups) == 1
    assert backups[0].exists()


def test_rebuild_from_archive(tmp_path):
    """Test rebuilding OPPM from a packed archive."""
    # Setup: create original OPPM directory and pack it
    original_root = tmp_path / "original" / ".oppm"
    apps_dir = original_root / "apps"
    shims_dir = original_root / "shims"
    meta_file = original_root / "meta.json"

    apps_dir.mkdir(parents=True)
    shims_dir.mkdir(parents=True)

    # Create test app
    test_app = apps_dir / "myapp"
    test_app.mkdir()
    (test_app / "myapp.exe").write_text("fake exe")

    # Create metadata with absolute path
    meta = {"apps": [{"name": "myapp", "relative_path": str(test_app.relative_to(original_root).as_posix())}]}
    meta_file.write_text(json.dumps(meta, indent=4))

    # Pack it
    config = OPPMConfig(root_dir=original_root, apps_dir=apps_dir, meta_file=meta_file, shims_dir=shims_dir)
    archive_path = tmp_path / "backup.tar.gz"
    pack(config, archive_path)

    # Rebuild to a new location
    new_root = tmp_path / "restored" / ".oppm"
    rebuild(archive_path, new_root)

    # Verify structure
    assert new_root.exists()
    assert (new_root / "apps" / "myapp" / "myapp.exe").exists()
    assert (new_root / "meta.json").exists()

    # Verify metadata uses relative paths (new format)
    new_meta = json.loads((new_root / "meta.json").read_text())
    assert len(new_meta["apps"]) == 1
    assert new_meta["apps"][0]["name"] == "myapp"
    assert new_meta["apps"][0]["relative_path"] == "apps/myapp"
    # Old 'path' field should be removed after migration
    assert "path" not in new_meta["apps"][0]


def test_rebuild_nonexistent_archive(tmp_path):
    """Test that rebuild raises error for nonexistent archive."""
    archive_path = tmp_path / "nonexistent.tar.gz"
    with pytest.raises(InvalidInputError, match="Archive not found"):
        rebuild(archive_path, tmp_path / "new")


def test_rebuild_invalid_archive(tmp_path):
    """Test that rebuild raises error for invalid archive."""
    # Create a non-archive file
    fake_archive = tmp_path / "fake.txt"
    fake_archive.write_text("not an archive file")

    with pytest.raises(InvalidInputError, match="Unsupported archive format"):
        rebuild(fake_archive, tmp_path / "new")


def test_rebuild_empty_archive(tmp_path):
    """Test that rebuild rejects an empty/invalid archive with proper error."""
    # Create an empty directory and pack it (invalid structure)
    empty_dir = tmp_path / "empty_source"
    empty_dir.mkdir()

    empty_archive = tmp_path / "empty"
    shutil.make_archive(str(empty_archive), "gztar", empty_dir)
    empty_archive_path = tmp_path / "empty.tar.gz"

    # Rebuild should fail with proper error message
    new_root = tmp_path / "new"
    with pytest.raises(RebuildError, match="Archive is invalid"):
        rebuild(empty_archive_path, new_root)


def test_rebuild_overwrites_with_confirmation(tmp_path, monkeypatch):
    """Test that rebuild asks for confirmation before overwriting."""
    # Setup: create archive
    original_root = tmp_path / "original" / ".oppm"
    apps_dir = original_root / "apps"
    meta_file = original_root / "meta.json"
    shims_dir = original_root / "shims"
    apps_dir.mkdir(parents=True)
    meta_file.write_text(json.dumps({"apps": []}))

    config = OPPMConfig(root_dir=original_root, apps_dir=apps_dir, meta_file=meta_file, shims_dir=shims_dir)
    archive_path = tmp_path / "backup.tar.gz"
    pack(config, archive_path)

    # Create existing target directory with content
    existing_target = tmp_path / "existing" / ".oppm"
    existing_target.mkdir(parents=True)
    (existing_target / "some_file.txt").write_text("existing content")

    # Mock user input to decline
    monkeypatch.setattr("builtins.input", lambda _: "n")

    # Should not overwrite
    rebuild(archive_path, existing_target)

    # Verify original content still exists
    assert (existing_target / "some_file.txt").exists()


def test_rebuild_updates_multiple_apps(tmp_path):
    """Test that rebuild correctly updates paths for multiple apps."""
    # Setup: create OPPM with multiple apps
    original_root = tmp_path / "original" / ".oppm"
    apps_dir = original_root / "apps"
    meta_file = original_root / "meta.json"
    shims_dir = original_root / "shims"
    apps_dir.mkdir(parents=True)

    # Create multiple apps
    for app_name in ["app1", "app2", "app3"]:
        app_dir = apps_dir / app_name
        app_dir.mkdir()
        (app_dir / f"{app_name}.exe").write_text("fake")

    # Create metadata
    meta = {
        "apps": [
            {"name": "app1", "relative_path": str((apps_dir / "app1").relative_to(original_root).as_posix())},
            {"name": "app2", "relative_path": str((apps_dir / "app2").relative_to(original_root).as_posix())},
            {"name": "app3", "relative_path": str((apps_dir / "app3").relative_to(original_root).as_posix())},
        ]
    }
    meta_file.write_text(json.dumps(meta, indent=4))

    # Pack and rebuild
    config = OPPMConfig(root_dir=original_root, apps_dir=apps_dir, meta_file=meta_file, shims_dir=shims_dir)
    archive_path = tmp_path / "backup.tar.gz"
    pack(config, archive_path)

    new_root = tmp_path / "new_location" / ".oppm"
    rebuild(archive_path, new_root)

    # Verify all apps are present and use relative paths
    new_meta = json.loads((new_root / "meta.json").read_text())
    assert len(new_meta["apps"]) == 3

    for app in new_meta["apps"]:
        app_name = app["name"]
        expected_relative_path = f"apps/{app_name}"
        assert app["relative_path"] == expected_relative_path
        # Verify old 'path' field is removed
        assert "path" not in app
        assert (new_root / "apps" / app_name / f"{app_name}.exe").exists()
