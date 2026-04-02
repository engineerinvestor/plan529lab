"""Custom exceptions for plan529lab."""


class Plan529LabError(Exception):
    """Base exception for plan529lab."""


class ValidationError(Plan529LabError):
    """Raised when input validation fails."""


class ConfigLoadError(Plan529LabError):
    """Raised when a configuration file cannot be loaded or parsed."""


class BreakEvenUndefinedError(Plan529LabError):
    """Raised when break-even probability is mathematically undefined."""
