"""Tests for shim management."""

import sys
from pathlib import Path

import pytest

from oppm.exceptions import ShimError
from oppm.shims import create_shim, list_shims, remove_shims_for_app


@pytest.fixture
def temp_shims_dir(tmp_path):
    """Create a temporary shims directory."""
    shims_dir = tmp_path / "shims"
    shims_dir.mkdir()
    return shims_dir


@pytest.fixture
def temp_exe(tmp_path):
    """Create a temporary executable file."""
    exe_path = tmp_path / "apps" / "myapp" / "myapp.exe"
    exe_path.parent.mkdir(parents=True)
    exe_path.write_text("fake exe")
    return exe_path


@pytest.fixture
def temp_app_dir(tmp_path):
    """Create a temporary app directory with multiple executables."""
    app_dir = tmp_path / "apps" / "myapp"
    app_dir.mkdir(parents=True)

    # Create multiple executables
    (app_dir / "main.exe").write_text("main")
    (app_dir / "helper.exe").write_text("helper")

    return app_dir


@pytest.mark.skipif(sys.platform == "win32", reason="Requires admin rights on Windows")
def test_create_shim_basic(temp_exe, temp_shims_dir):
    """Test creating a basic shim."""
    shim_name = "myshim.exe"

    create_shim(temp_exe, shim_name, temp_shims_dir)

    shim_path = temp_shims_dir / shim_name
    assert shim_path.exists()
    assert shim_path.is_symlink()
    assert shim_path.resolve() == temp_exe.resolve()


@pytest.mark.skipif(sys.platform == "win32", reason="Requires admin rights on Windows")
def test_create_shim_already_exists(temp_exe, temp_shims_dir):
    """Test creating a shim when one already exists."""
    shim_name = "myshim.exe"

    # Create first shim
    create_shim(temp_exe, shim_name, temp_shims_dir)

    # Try to create again
    with pytest.raises(ShimError, match="already exists"):
        create_shim(temp_exe, shim_name, temp_shims_dir)


@pytest.mark.skipif(sys.platform == "win32", reason="Requires admin rights on Windows")
def test_create_shim_creates_directory(tmp_path, temp_exe):
    """Test that create_shim creates the shims directory if it doesn't exist."""
    shims_dir = tmp_path / "nonexistent_shims"
    assert not shims_dir.exists()

    create_shim(temp_exe, "test.exe", shims_dir)

    assert shims_dir.exists()
    assert shims_dir.is_dir()


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")
def test_create_shim_windows_permissions(temp_exe, temp_shims_dir):
    """Test shim creation on Windows (requires admin or dev mode)."""
    try:
        create_shim(temp_exe, "test.exe", temp_shims_dir)
        # If it succeeds, verify the shim
        assert (temp_shims_dir / "test.exe").exists()
    except ShimError as e:
        # Expected on Windows without admin rights
        assert "Administrator" in str(e) or "Developer Mode" in str(e)


def test_list_shims_empty(temp_shims_dir):
    """Test listing shims in an empty directory."""
    shims = list_shims(temp_shims_dir)
    assert shims == []


def test_list_shims_nonexistent_directory(tmp_path):
    """Test listing shims in a non-existent directory."""
    nonexistent = tmp_path / "nonexistent"
    shims = list_shims(nonexistent)
    assert shims == []


@pytest.mark.skipif(sys.platform == "win32", reason="Requires admin rights on Windows")
def test_list_shims_with_shims(temp_exe, temp_shims_dir):
    """Test listing shims when shims exist."""
    # Create multiple shims
    create_shim(temp_exe, "shim1.exe", temp_shims_dir)

    temp_exe2 = temp_exe.parent / "another.exe"
    temp_exe2.write_text("another")
    create_shim(temp_exe2, "shim2.exe", temp_shims_dir)

    shims = list_shims(temp_shims_dir)

    assert len(shims) == 2
    shim_names = [name for name, _ in shims]
    assert "shim1.exe" in shim_names
    assert "shim2.exe" in shim_names


@pytest.mark.skipif(sys.platform == "win32", reason="Requires admin rights on Windows")
def test_list_shims_sorted(temp_exe, temp_shims_dir):
    """Test that listed shims are sorted by name."""
    # Create shims in non-alphabetical order
    for name in ["zebra.exe", "apple.exe", "middle.exe"]:
        exe = temp_exe.parent / name
        exe.write_text("content")
        create_shim(exe, name, temp_shims_dir)

    shims = list_shims(temp_shims_dir)
    shim_names = [name for name, _ in shims]

    assert shim_names == ["apple.exe", "middle.exe", "zebra.exe"]


def test_list_shims_ignores_regular_files(temp_shims_dir):
    """Test that list_shims ignores regular files."""
    # Create a regular file (not a symlink)
    regular_file = temp_shims_dir / "regular.txt"
    regular_file.write_text("not a shim")

    shims = list_shims(temp_shims_dir)
    assert len(shims) == 0


@pytest.mark.skipif(sys.platform == "win32", reason="Requires admin rights on Windows")
def test_remove_shims_for_app_basic(temp_app_dir, temp_shims_dir):
    """Test removing shims for an app."""
    # Create shims pointing to app executables
    main_exe = temp_app_dir / "main.exe"
    helper_exe = temp_app_dir / "helper.exe"

    create_shim(main_exe, "main.exe", temp_shims_dir)
    create_shim(helper_exe, "helper.exe", temp_shims_dir)

    # Verify shims exist
    assert len(list_shims(temp_shims_dir)) == 2

    # Remove shims
    remove_shims_for_app(temp_app_dir, temp_shims_dir)

    # Verify shims are removed
    assert len(list_shims(temp_shims_dir)) == 0


@pytest.mark.skipif(sys.platform == "win32", reason="Requires admin rights on Windows")
def test_remove_shims_for_app_keeps_others(temp_app_dir, temp_shims_dir, tmp_path):
    """Test that removing shims for one app doesn't affect other apps."""
    # Create shims for the test app
    create_shim(temp_app_dir / "main.exe", "main.exe", temp_shims_dir)

    # Create shims for another app
    other_app_dir = tmp_path / "apps" / "otherapp"
    other_app_dir.mkdir(parents=True)
    other_exe = other_app_dir / "other.exe"
    other_exe.write_text("other")
    create_shim(other_exe, "other.exe", temp_shims_dir)

    # Remove shims for test app
    remove_shims_for_app(temp_app_dir, temp_shims_dir)

    # Verify only other app's shim remains
    remaining_shims = list_shims(temp_shims_dir)
    assert len(remaining_shims) == 1
    assert remaining_shims[0][0] == "other.exe"


def test_remove_shims_for_app_nonexistent_dir(temp_app_dir, tmp_path):
    """Test removing shims when shims directory doesn't exist."""
    nonexistent_shims = tmp_path / "nonexistent_shims"

    # Should not raise an error
    remove_shims_for_app(temp_app_dir, nonexistent_shims)


def test_remove_shims_for_app_empty_dir(temp_app_dir, temp_shims_dir):
    """Test removing shims from an empty directory."""
    # Should not raise an error
    remove_shims_for_app(temp_app_dir, temp_shims_dir)
