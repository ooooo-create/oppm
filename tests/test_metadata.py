"""Tests for metadata management."""

import json
import tempfile
from pathlib import Path

import pytest

from oppm.exceptions import MetaFileError
from oppm.metadata import (
    AppEntry,
    Metadata,
    add_app_to_metadata,
    load_metadata,
    remove_app_from_metadata,
    save_metadata,
)


@pytest.fixture
def temp_meta_file(tmp_path):
    """Create a temporary metadata file path."""
    return tmp_path / "meta.json"


@pytest.fixture
def sample_metadata() -> Metadata:
    """Create sample metadata with relative paths."""
    return {
        "apps": [
            {"name": "app1", "relative_path": "apps/app1"},
            {"name": "app2", "relative_path": "apps/app2"},
        ]
    }


def test_save_metadata_creates_file(temp_meta_file, sample_metadata):
    """Test that save_metadata creates a file."""
    assert not temp_meta_file.exists()

    save_metadata(temp_meta_file, sample_metadata)

    assert temp_meta_file.exists()
    assert temp_meta_file.is_file()


def test_save_and_load_metadata(temp_meta_file, sample_metadata):
    """Test saving and loading metadata."""
    save_metadata(temp_meta_file, sample_metadata)

    loaded = load_metadata(temp_meta_file)

    assert loaded == sample_metadata
    assert len(loaded["apps"]) == 2
    assert loaded["apps"][0]["name"] == "app1"


def test_load_nonexistent_metadata(temp_meta_file):
    """Test loading metadata when file doesn't exist."""
    with pytest.raises(MetaFileError, match="Metadata file does not exist"):
        load_metadata(temp_meta_file)


def test_load_invalid_json(temp_meta_file):
    """Test loading invalid JSON metadata."""
    temp_meta_file.write_text("not valid json {{{")

    with pytest.raises(MetaFileError, match="Failed to read or parse"):
        load_metadata(temp_meta_file)


def test_save_metadata_with_unicode(temp_meta_file):
    """Test saving metadata with unicode characters."""
    metadata: Metadata = {
        "apps": [
            {"name": "中文应用", "relative_path": "/path/to/中文应用"},
            {"name": "日本語アプリ", "relative_path": "/path/to/日本語"},
        ]
    }

    save_metadata(temp_meta_file, metadata)
    loaded = load_metadata(temp_meta_file)

    assert loaded["apps"][0]["name"] == "中文应用"
    assert loaded["apps"][1]["name"] == "日本語アプリ"


def test_add_app_to_metadata_new_app(temp_meta_file, tmp_path):
    """Test adding a new app to metadata."""
    # Create initial metadata
    initial_meta: Metadata = {"apps": []}
    save_metadata(temp_meta_file, initial_meta)

    # Setup root and app directory
    root_dir = tmp_path / "root"
    root_dir.mkdir()
    app_dir = root_dir / "apps" / "newapp"
    app_dir.mkdir(parents=True)

    # Add app
    add_app_to_metadata("newapp", app_dir, root_dir, temp_meta_file)

    # Verify
    loaded = load_metadata(temp_meta_file)
    assert len(loaded["apps"]) == 1
    assert loaded["apps"][0]["name"] == "newapp"
    assert loaded["apps"][0]["relative_path"] == "apps/newapp"


def test_add_app_to_metadata_replace_existing(temp_meta_file, tmp_path):
    """Test that adding an app with existing name replaces it."""
    # Create sample metadata with relative paths
    sample_metadata: Metadata = {
        "apps": [
            {"name": "app1", "relative_path": "apps/app1"},
            {"name": "app2", "relative_path": "apps/app2"},
        ]
    }
    save_metadata(temp_meta_file, sample_metadata)

    # Setup root and app directory
    root_dir = tmp_path / "root"
    root_dir.mkdir()
    new_app_dir = root_dir / "apps" / "app1"
    new_app_dir.mkdir(parents=True)

    # Add app with same name but different path structure
    add_app_to_metadata("app1", new_app_dir, root_dir, temp_meta_file)

    # Verify
    loaded = load_metadata(temp_meta_file)
    assert len(loaded["apps"]) == 2  # Still 2 apps
    app1_entries = [app for app in loaded["apps"] if app["name"] == "app1"]
    assert len(app1_entries) == 1  # Only one app1
    assert app1_entries[0]["relative_path"] == "apps/app1"


def test_remove_app_from_metadata_existing(temp_meta_file, sample_metadata):
    """Test removing an existing app from metadata."""
    save_metadata(temp_meta_file, sample_metadata)

    result = remove_app_from_metadata("app1", temp_meta_file)

    assert result is True
    loaded = load_metadata(temp_meta_file)
    assert len(loaded["apps"]) == 1
    assert loaded["apps"][0]["name"] == "app2"


def test_remove_app_from_metadata_nonexistent(temp_meta_file, sample_metadata):
    """Test removing a non-existent app from metadata."""
    save_metadata(temp_meta_file, sample_metadata)

    result = remove_app_from_metadata("nonexistent", temp_meta_file)

    assert result is False
    loaded = load_metadata(temp_meta_file)
    assert len(loaded["apps"]) == 2  # No change


def test_metadata_preserves_order(temp_meta_file):
    """Test that metadata preserves insertion order."""
    metadata: Metadata = {
        "apps": [
            {"name": "app_a", "relative_path": "apps/a"},
            {"name": "app_z", "relative_path": "apps/z"},
            {"name": "app_m", "relative_path": "apps/m"},
        ]
    }

    save_metadata(temp_meta_file, metadata)
    loaded = load_metadata(temp_meta_file)

    names = [app["name"] for app in loaded["apps"]]
    assert names == ["app_a", "app_z", "app_m"]


def test_metadata_json_formatting(temp_meta_file, sample_metadata):
    """Test that saved JSON is properly formatted."""
    save_metadata(temp_meta_file, sample_metadata)

    content = temp_meta_file.read_text(encoding="utf-8")

    # Should be indented
    assert "    " in content
    # Should have "apps" key
    assert '"apps"' in content
    # Should be valid JSON
    parsed = json.loads(content)
    assert "apps" in parsed
