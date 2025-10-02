"""Tests for custom exceptions."""

import pytest

from oppm.exceptions import (
    AppNotFoundError,
    ConfigError,
    InstallError,
    InvalidInputError,
    MetaFileError,
    MigrationError,
    OPPMError,
    PackError,
    RebuildError,
    ShimError,
)


def test_oppm_error_is_base_exception():
    """Test that OPPMError is the base exception."""
    error = OPPMError("test message")
    assert isinstance(error, Exception)
    assert str(error) == "test message"


def test_all_exceptions_inherit_from_oppm_error():
    """Test that all custom exceptions inherit from OPPMError."""
    exceptions = [
        MetaFileError,
        AppNotFoundError,
        ConfigError,
        ShimError,
        InstallError,
        InvalidInputError,
        MigrationError,
        PackError,
        RebuildError,
    ]

    for exc_class in exceptions:
        error = exc_class("test")
        assert isinstance(error, OPPMError)
        assert isinstance(error, Exception)


def test_exception_messages():
    """Test that exceptions preserve their messages."""
    message = "This is a test error message"

    exceptions = [
        OPPMError(message),
        MetaFileError(message),
        AppNotFoundError(message),
        ConfigError(message),
        ShimError(message),
        InstallError(message),
        InvalidInputError(message),
        MigrationError(message),
        PackError(message),
        RebuildError(message),
    ]

    for error in exceptions:
        assert str(error) == message


def test_exception_can_be_caught_as_oppm_error():
    """Test that all exceptions can be caught as OPPMError."""
    exceptions = [
        MetaFileError("meta"),
        AppNotFoundError("app"),
        ConfigError("config"),
        ShimError("shim"),
        InstallError("install"),
        InvalidInputError("input"),
        MigrationError("migrate"),
        PackError("pack"),
        RebuildError("rebuild"),
    ]

    for error in exceptions:
        try:
            raise error
        except OPPMError:
            pass  # Successfully caught as OPPMError
        else:
            pytest.fail(f"{type(error).__name__} was not caught as OPPMError")


def test_exception_hierarchy():
    """Test the exception hierarchy structure."""
    # Create instances
    base_error = OPPMError("base")
    install_error = InstallError("install")

    # Test inheritance
    assert isinstance(install_error, OPPMError)
    assert isinstance(install_error, Exception)
    assert not isinstance(base_error, InstallError)


def test_exception_with_cause():
    """Test exceptions with __cause__ (chained exceptions)."""
    try:
        try:
            raise ValueError("Original error")
        except ValueError as e:
            raise InstallError("Installation failed") from e
    except InstallError as install_err:
        assert install_err.__cause__ is not None
        assert isinstance(install_err.__cause__, ValueError)
        assert str(install_err.__cause__) == "Original error"


def test_meta_file_error():
    """Test MetaFileError specific behavior."""
    error = MetaFileError("Failed to read meta.json")
    assert "meta.json" in str(error)


def test_app_not_found_error():
    """Test AppNotFoundError specific behavior."""
    app_name = "myapp"
    error = AppNotFoundError(f"Application '{app_name}' not found")
    assert app_name in str(error)


def test_config_error():
    """Test ConfigError specific behavior."""
    error = ConfigError("Configuration is invalid")
    assert "Configuration" in str(error)


def test_shim_error():
    """Test ShimError specific behavior."""
    error = ShimError("Failed to create shim")
    assert "shim" in str(error)


def test_install_error():
    """Test InstallError specific behavior."""
    error = InstallError("Installation failed due to missing file")
    assert "Installation" in str(error)


def test_invalid_input_error():
    """Test InvalidInputError specific behavior."""
    error = InvalidInputError("Invalid file type: .xyz")
    assert "Invalid" in str(error)


def test_migration_error():
    """Test MigrationError specific behavior."""
    error = MigrationError("Failed to migrate directory")
    assert "migrate" in str(error)


def test_pack_error():
    """Test PackError specific behavior."""
    error = PackError("Failed to pack directory")
    assert "pack" in str(error)


def test_rebuild_error():
    """Test RebuildError specific behavior."""
    error = RebuildError("Failed to rebuild from archive")
    assert "rebuild" in str(error)
