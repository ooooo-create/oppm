"""Custom exceptions for OPPM."""


class OPPMError(Exception):
    """Base exception for all OPPM errors."""

    pass


class MetaFileError(OPPMError):
    """Error related to meta.json file operations."""

    pass


class AppNotFoundError(OPPMError):
    """Raised when the specified application is not found."""

    pass


class ConfigError(OPPMError):
    """Error related to configuration file operations."""

    pass


class ShimError(OPPMError):
    """Error related to shim operations."""

    pass


class InstallError(OPPMError):
    """Error during application installation."""

    pass


class InvalidInputError(OPPMError):
    """Error when input path or format is invalid."""

    pass


class MigrationError(OPPMError):
    """Error during directory migration."""

    pass


class PackError(OPPMError):
    """Error during pack/backup operations."""

    pass


class RebuildError(OPPMError):
    """Error during rebuild/restore operations."""

    pass
