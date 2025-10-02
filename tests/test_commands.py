"""Integration tests for OPPM commands."""

import shutil
import sys
import tempfile
from pathlib import Path

import pytest

from oppm.commands import (
    _extract_app_name_from_path,
    add_executable,
    clean_all,
    delete_executable,
    initialize,
    install_app,
    list_apps,
    migrate_root,
    remove_app,
    show_shims,
    update_metadata,
)
from oppm.config import OPPMConfig, load_config, save_config
from oppm.exceptions import (
    AppNotFoundError,
    InstallError,
    InvalidInputError,
    MigrationError,
)
from oppm.metadata import load_metadata


@pytest.fixture
def temp_oppm_root(tmp_path):
    """Create a temporary OPPM root directory."""
    root = tmp_path / "oppm_root"
    root.mkdir()
    return root


@pytest.fixture
def oppm_config(temp_oppm_root):
    """Create a test OPPM configuration."""
    config = OPPMConfig(
        root_dir=temp_oppm_root,
        apps_dir=temp_oppm_root / "apps",
        meta_file=temp_oppm_root / "meta.json",
        shims_dir=temp_oppm_root / "shims",
    )

    # Create necessary directories
    config.apps_dir.mkdir()
    config.shims_dir.mkdir()

    # Create metadata file
    from oppm.metadata import save_metadata

    save_metadata(config.meta_file, {"apps": []})

    return config


@pytest.fixture
def sample_exe(tmp_path):
    """Create a sample executable file for install tests."""
    exe_path = tmp_path / "sample.exe"
    exe_path.write_text("fake executable")
    return exe_path


@pytest.fixture
def installed_exe(oppm_config):
    """Create a sample executable file inside apps directory for exe management tests."""
    # Create a dummy app directory
    app_dir = oppm_config.apps_dir / "sample_app"
    app_dir.mkdir(parents=True, exist_ok=True)

    exe_path = app_dir / "sample.exe"
    exe_path.write_text("fake executable")
    return exe_path


@pytest.fixture
def sample_dir(tmp_path):
    """Create a sample directory with files."""
    app_dir = tmp_path / "sample_app"
    app_dir.mkdir()
    (app_dir / "main.exe").write_text("main")
    (app_dir / "config.ini").write_text("config")
    return app_dir


class TestExtractAppName:
    """Tests for _extract_app_name_from_path function."""

    def test_extract_from_directory(self, sample_dir):
        """Test extracting name from directory."""
        name = _extract_app_name_from_path(sample_dir)
        assert name == "sample_app"

    def test_extract_from_exe(self, sample_exe):
        """Test extracting name from .exe file."""
        name = _extract_app_name_from_path(sample_exe)
        assert name == "sample"

    def test_extract_from_zip(self, tmp_path):
        """Test extracting name from .zip file."""
        zip_file = tmp_path / "myapp.zip"
        zip_file.write_text("fake zip")

        name = _extract_app_name_from_path(zip_file)
        assert name == "myapp"

    def test_extract_from_tar_gz(self, tmp_path):
        """Test extracting name from .tar.gz file."""
        tar_file = tmp_path / "myapp.tar.gz"
        tar_file.write_text("fake tar")

        name = _extract_app_name_from_path(tar_file)
        assert name == "myapp"

    def test_unsupported_type_raises_error(self, tmp_path):
        """Test that unsupported file types raise InvalidInputError."""
        unsupported = tmp_path / "file.xyz"
        unsupported.write_text("content")

        with pytest.raises(InvalidInputError, match="Unsupported file type"):
            _extract_app_name_from_path(unsupported)


class TestInstallApp:
    """Tests for install_app function."""

    def test_install_exe(self, sample_exe, oppm_config):
        """Test installing an executable."""
        install_app(sample_exe, oppm_config)

        # Verify app directory was created
        app_dir = oppm_config.apps_dir / "sample"
        assert app_dir.exists()
        assert (app_dir / "sample.exe").exists()

        # Verify metadata was updated
        meta = load_metadata(oppm_config.meta_file)
        assert len(meta["apps"]) == 1
        assert meta["apps"][0]["name"] == "sample"

    def test_install_directory(self, sample_dir, oppm_config):
        """Test installing a directory."""
        install_app(sample_dir, oppm_config)

        # Verify app directory was created
        app_dir = oppm_config.apps_dir / "sample_app"
        assert app_dir.exists()
        assert (app_dir / "main.exe").exists()
        assert (app_dir / "config.ini").exists()

    def test_install_with_custom_name(self, sample_exe, oppm_config):
        """Test installing with a custom name."""
        install_app(sample_exe, oppm_config, name="myapp")

        app_dir = oppm_config.apps_dir / "myapp"
        assert app_dir.exists()

        meta = load_metadata(oppm_config.meta_file)
        assert meta["apps"][0]["name"] == "myapp"

    def test_install_nonexistent_raises_error(self, oppm_config, tmp_path):
        """Test installing non-existent file raises error."""
        nonexistent = tmp_path / "nonexistent.exe"

        with pytest.raises(InvalidInputError, match="does not exist"):
            install_app(nonexistent, oppm_config)

    def test_install_replaces_existing(self, sample_exe, oppm_config):
        """Test that installing over existing app replaces it."""
        # Install first time
        install_app(sample_exe, oppm_config)

        # Modify the exe
        sample_exe.write_text("modified content")

        # Install again
        install_app(sample_exe, oppm_config)

        # Verify only one app in metadata
        meta = load_metadata(oppm_config.meta_file)
        assert len(meta["apps"]) == 1

        # Verify content was updated
        app_exe = oppm_config.apps_dir / "sample" / "sample.exe"
        assert app_exe.read_text() == "modified content"


class TestListApps:
    """Tests for list_apps function."""

    def test_list_empty(self, oppm_config, capsys):
        """Test listing when no apps are installed."""
        list_apps(oppm_config)

        captured = capsys.readouterr()
        assert "No applications installed" in captured.out

    def test_list_apps(self, oppm_config, sample_exe, capsys):
        """Test listing installed apps."""
        # Install some apps
        install_app(sample_exe, oppm_config)

        # Create another app
        exe2 = sample_exe.parent / "another.exe"
        exe2.write_text("another")
        install_app(exe2, oppm_config, name="otherapp")

        # List apps
        list_apps(oppm_config)

        captured = capsys.readouterr()
        assert "sample" in captured.out
        assert "otherapp" in captured.out


class TestRemoveApp:
    """Tests for remove_app function."""

    def test_remove_existing_app(self, oppm_config, sample_exe):
        """Test removing an existing app."""
        # Install first
        install_app(sample_exe, oppm_config)

        # Remove
        remove_app("sample", oppm_config)

        # Verify app directory is gone
        app_dir = oppm_config.apps_dir / "sample"
        assert not app_dir.exists()

        # Verify metadata is updated
        meta = load_metadata(oppm_config.meta_file)
        assert len(meta["apps"]) == 0

    def test_remove_nonexistent_raises_error(self, oppm_config):
        """Test removing non-existent app raises error."""
        with pytest.raises(AppNotFoundError, match="not found"):
            remove_app("nonexistent", oppm_config)


class TestUpdateMetadata:
    """Tests for update_metadata function."""

    def test_update_adds_missing_apps(self, oppm_config, capsys):
        """Test that update adds apps missing from metadata."""
        # Create an app directory manually (bypassing install)
        app_dir = oppm_config.apps_dir / "manual_app"
        app_dir.mkdir()
        (app_dir / "app.exe").write_text("content")

        # Update metadata
        update_metadata(oppm_config)

        # Verify app was added
        meta = load_metadata(oppm_config.meta_file)
        assert len(meta["apps"]) == 1
        assert meta["apps"][0]["name"] == "manual_app"

        captured = capsys.readouterr()
        assert "1 apps to add" in captured.out

    def test_update_removes_missing_dirs(self, oppm_config, sample_exe, capsys):
        """Test that update removes apps whose directories are gone."""
        # Install an app (it will be installed as "sample")
        install_app(sample_exe, oppm_config)

        # Manually remove the installed directory
        app_dir = oppm_config.apps_dir / "sample"
        shutil.rmtree(app_dir)

        # Update metadata
        update_metadata(oppm_config)

        # Verify app was removed from metadata
        meta = load_metadata(oppm_config.meta_file)
        assert len(meta["apps"]) == 0

        captured = capsys.readouterr()
        assert "1 apps to remove" in captured.out


class TestCleanAll:
    """Tests for clean_all function."""

    def test_clean_removes_all_apps(self, oppm_config, sample_exe):
        """Test that clean removes all apps."""
        # Install some apps
        install_app(sample_exe, oppm_config)

        exe2 = sample_exe.parent / "another.exe"
        exe2.write_text("another")
        install_app(exe2, oppm_config, name="another")

        # Clean
        clean_all(oppm_config)

        # Verify all apps are gone
        assert list(oppm_config.apps_dir.iterdir()) == []

        # Verify metadata is empty
        meta = load_metadata(oppm_config.meta_file)
        assert len(meta["apps"]) == 0


class TestInitialize:
    """Tests for initialize function."""

    def test_initialize_creates_structure(self, tmp_path, capsys):
        """Test that initialize creates the directory structure."""
        root = tmp_path / "new_oppm"

        initialize(root)

        # Verify directories exist
        assert root.exists()
        assert (root / "apps").exists()
        assert (root / "shims").exists()
        assert (root / "meta.json").exists()

        # Verify instructions were printed
        captured = capsys.readouterr()
        assert "IMPORTANT NEXT STEP" in captured.out


class TestMigrateRoot:
    """Tests for migrate_root function."""

    def test_migrate_moves_directory(self, oppm_config, sample_exe, tmp_path):
        """Test that migrate moves the root directory."""
        # Save initial config (needed for update_config in migrate)
        save_config(oppm_config)

        # Install an app
        install_app(sample_exe, oppm_config)

        # Migrate
        new_root = tmp_path / "new_oppm_root"
        migrate_root(oppm_config.root_dir, new_root)

        # Verify old root is gone
        assert not oppm_config.root_dir.exists()

        # Verify new root exists with correct structure
        assert new_root.exists()
        assert (new_root / "apps").exists()
        assert (new_root / "apps" / "sample").exists()

    def test_migrate_to_same_location(self, oppm_config, capsys):
        """Test migrating to the same location."""
        migrate_root(oppm_config.root_dir, oppm_config.root_dir)

        captured = capsys.readouterr()
        assert "same" in captured.out.lower()

    def test_migrate_nonexistent_source_raises_error(self, tmp_path):
        """Test migrating from non-existent directory raises error."""
        nonexistent = tmp_path / "nonexistent"
        new_root = tmp_path / "new_root"

        with pytest.raises(MigrationError, match="does not exist"):
            migrate_root(nonexistent, new_root)

    def test_migrate_to_nonempty_target_raises_error(self, oppm_config, tmp_path):
        """Test migrating to non-empty directory raises error."""
        target = tmp_path / "target"
        target.mkdir()
        (target / "existing_file.txt").write_text("content")

        with pytest.raises(MigrationError, match="not empty"):
            migrate_root(oppm_config.root_dir, target)


class TestExecutableManagement:
    """Tests for add_executable, delete_executable, and show_shims."""

    @pytest.mark.skipif(sys.platform == "win32", reason="Requires admin rights on Windows")
    def test_add_executable(self, oppm_config, installed_exe, capsys):
        """Test adding an executable."""
        add_executable(installed_exe, None, oppm_config)

        captured = capsys.readouterr()
        assert "Successfully added" in captured.out

    @pytest.mark.skipif(sys.platform == "win32", reason="Requires admin rights on Windows")
    def test_add_executable_with_custom_name(self, oppm_config, installed_exe):
        """Test adding executable with custom name."""
        add_executable(installed_exe, "myshim.exe", oppm_config)

        # Verify shim was created
        from oppm.shims import list_shims

        shims = list_shims(oppm_config.shims_dir)
        assert len(shims) == 1
        assert shims[0][0] == "myshim.exe"

    def test_add_nonexistent_executable_raises_error(self, oppm_config, tmp_path):
        """Test adding non-existent executable raises error."""
        nonexistent = tmp_path / "nonexistent.exe"

        with pytest.raises(InvalidInputError, match="not found"):
            add_executable(nonexistent, None, oppm_config)

    def test_delete_executable_nonexistent_raises_error(self, oppm_config):
        """Test deleting non-existent shim raises error."""
        with pytest.raises(InvalidInputError, match="Shim not found"):
            delete_executable("nonexistent.exe", oppm_config)

    @pytest.mark.skipif(sys.platform == "win32", reason="Requires admin rights on Windows")
    def test_delete_executable_existing_shim(self, oppm_config, installed_exe, capsys):
        """Test deleting an existing shim."""
        # Add a shim first
        add_executable(installed_exe, "myshim.exe", oppm_config)

        # Delete the shim
        delete_executable("myshim.exe", oppm_config)

        captured = capsys.readouterr()
        assert "Successfully deleted shim: myshim.exe" in captured.out

        # Verify shim is gone
        from oppm.shims import list_shims

        shims = list_shims(oppm_config.shims_dir)
        assert len(shims) == 0

    def test_show_shims_empty(self, oppm_config, capsys):
        """Test showing shims when none exist."""
        show_shims(oppm_config)

        captured = capsys.readouterr()
        assert "No shims found" in captured.out

    @pytest.mark.skipif(sys.platform == "win32", reason="Requires admin rights on Windows")
    def test_show_shims_with_shims(self, oppm_config, installed_exe, capsys):
        """Test showing existing shims."""
        # Add a shim
        add_executable(installed_exe, None, oppm_config)

        # Show shims
        show_shims(oppm_config)

        captured = capsys.readouterr()
        assert "Installed shims" in captured.out
        assert "sample.exe" in captured.out
