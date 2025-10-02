"""Shared pytest configuration and fixtures for all tests."""

import os
import tempfile
from pathlib import Path

import pytest

# Set test config file BEFORE any oppm modules are imported
# This ensures CONFIG_FILE in config.py uses the test path
_test_config_dir = Path(tempfile.mkdtemp(prefix="oppm_test_"))
os.environ["OPPM_CONFIG_FILE"] = str(_test_config_dir / ".oppmconfig_test")
