"""Tests for configuration management."""

from pathlib import Path

import pytest

from oppm.config import CONFIG_FILE, OPPMConfig, load_config, save_config, update_config
from oppm.exceptions import ConfigError


@pytest.fixture
def temp_config_file(monkeypatch, tmp_path):
    """Get a unique config file path for this test."""
    # Each test gets its own unique config file path
    temp_config = tmp_path / ".oppmconfig"
    monkeypatch.setattr("oppm.config.CONFIG_FILE", temp_config)
    return temp_config


@pytest.fixture
def sample_config(tmp_path):
    """Create a sample configuration."""
    root_dir = tmp_path / "oppm_root"
    return OPPMConfig(
        root_dir=root_dir,
        apps_dir=root_dir / "apps",
        meta_file=root_dir / "meta.json",
        shims_dir=root_dir / "shims",
    )


def test_oppm_config_namedtuple(sample_config):
    """Test OPPMConfig NamedTuple properties."""
    assert sample_config.root_dir.name == "oppm_root"
    assert sample_config.apps_dir.name == "apps"
    assert sample_config.meta_file.name == "meta.json"
    assert sample_config.shims_dir.name == "shims"
    assert sample_config.shims_dir == sample_config.root_dir / "shims"


def test_save_config_creates_file(temp_config_file, sample_config):
    """Test that save_config creates a config file."""
    assert not temp_config_file.exists()

    save_config(sample_config)

    assert temp_config_file.exists()
    assert temp_config_file.is_file()


def test_save_and_load_config(temp_config_file, sample_config):
    """Test saving and loading configuration."""
    save_config(sample_config)

    loaded_config = load_config()

    assert loaded_config.root_dir == sample_config.root_dir
    assert loaded_config.apps_dir == sample_config.apps_dir
    assert loaded_config.meta_file == sample_config.meta_file


def test_load_config_without_file(temp_config_file):
    """Test loading config when file doesn't exist."""
    assert not temp_config_file.exists()

    with pytest.raises(ConfigError, match="Configuration file does not exist"):
        load_config()


def test_update_config(temp_config_file, sample_config, tmp_path):
    """Test updating an existing configuration."""
    # Save initial config
    save_config(sample_config)

    # Create new config with different paths
    new_root = tmp_path / "new_oppm_root"
    new_config = OPPMConfig(
        root_dir=new_root,
        apps_dir=new_root / "apps",
        meta_file=new_root / "meta.json",
        shims_dir=new_root / "shims",
    )

    # Update config
    update_config(new_config)

    # Load and verify
    loaded_config = load_config()
    assert loaded_config.root_dir == new_root
    assert loaded_config.apps_dir == new_root / "apps"


def test_config_file_structure(temp_config_file, sample_config):
    """Test the structure of saved config file."""
    save_config(sample_config)

    content = temp_config_file.read_text()

    assert "[config]" in content
    assert "root_dir" in content
    assert "apps_dir" in content
    assert "meta_file" in content
    # On Windows, paths are escaped with double backslashes in TOML
    assert "root_dir" in content and "oppm_root" in content
