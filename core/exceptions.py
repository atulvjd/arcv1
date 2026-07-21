"""
ArcV1 Exception Hierarchy
"""

from __future__ import annotations


class ArcV1Error(Exception):
    """Base exception for all ArcV1 errors."""

    pass


class ConfigurationError(ArcV1Error):
    """Raised when configuration is invalid."""

    pass


class RegistryError(ArcV1Error):
    """Raised for registry-related errors."""

    pass


class RuntimeError(ArcV1Error):
    """Raised for runtime failures."""

    pass


class AgentError(ArcV1Error):
    """Raised for agent-related errors."""

    pass


class ToolError(ArcV1Error):
    """Raised for tool-related errors."""

    pass


class PermissionError(ArcV1Error):
    """Raised when permission is denied."""

    pass


class ModelError(ArcV1Error):
    """Raised for model-related errors."""

    pass


class EventError(ArcV1Error):
    """Raised for event system failures."""

    pass