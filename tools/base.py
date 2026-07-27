"""
ArcV1 Base Tool

Defines the abstract interface for all tools.
Every tool inherits BaseTool and provides metadata.
ToolService only manages tools; execution belongs here.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ToolCategory(Enum):
    """Categories for organizing tools."""
    FILESYSTEM = "filesystem"
    TERMINAL = "terminal"
    NETWORK = "network"
    DATABASE = "database"
    BROWSER = "browser"
    EMAIL = "email"
    GIT = "git"
    SEARCH = "search"
    DOCKER = "docker"
    CUSTOM = "custom"


@dataclass
class ToolParameter:
    """
    Describes a parameter for a tool.
    
    Attributes:
        name: Parameter name.
        type_name: Type (e.g., 'str', 'int', 'bool').
        description: Human-readable description.
        required: Whether this parameter is required.
        default: Default value if not required.
    """
    name: str
    type_name: str
    description: str = ""
    required: bool = True
    default: Any = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "type": self.type_name,
            "description": self.description,
            "required": self.required,
            "default": self.default
        }


@dataclass
class ToolMetadata:
    """
    Metadata describing a tool.
    
    Attributes:
        name: Unique tool name.
        description: Human-readable description.
        category: Tool category.
        parameters: List of parameters.
        return_type: Description of return value.
        permissions: Required permission strings.
        version: Tool version.
        author: Tool author.
    """
    name: str
    description: str = ""
    category: ToolCategory = ToolCategory.CUSTOM
    parameters: list[ToolParameter] = field(default_factory=list)
    return_type: str = "Any"
    permissions: list[str] = field(default_factory=list)
    version: str = "1.0.0"
    author: str = "ArcV1"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "parameters": [p.to_dict() for p in self.parameters],
            "return_type": self.return_type,
            "permissions": self.permissions,
            "version": self.version,
            "author": self.author
        }


@dataclass
class ToolResult:
    """
    Standardized result from tool execution.
    
    Attributes:
        success: Whether execution was successful.
        data: The result data (if successful).
        error: Error message (if failed).
        execution_time_ms: Duration in milliseconds.
        metadata: Additional result metadata.
    """
    success: bool
    data: Any = None
    error: str | None = None
    execution_time_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, data: Any, **metadata: Any) -> "ToolResult":
        """Create a successful result."""
        return cls(success=True, data=data, metadata=metadata)

    @classmethod
    def fail(cls, error: str, **metadata: Any) -> "ToolResult":
        """Create a failed result."""
        return cls(success=False, error=error, metadata=metadata)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "metadata": self.metadata
        }


class BaseTool(ABC):
    """
    Abstract base class for all tools.
    
    Tools implement execution logic and expose metadata.
    ToolService manages registration and dispatch.
    """
    
    def __init__(self, metadata: ToolMetadata) -> None:
        """
        Initialize the tool with its metadata.
        
        Args:
            metadata: Tool metadata describing its capabilities.
        """
        self._metadata = metadata
    
    @property
    def metadata(self) -> ToolMetadata:
        """Return tool metadata."""
        return self._metadata
    
    @property
    def name(self) -> str:
        """Return tool name (convenience)."""
        return self._metadata.name
    
    @abstractmethod
    def execute(self, **kwargs: Any) -> ToolResult:
        """
        Execute the tool with given parameters.
        
        Args:
            **kwargs: Tool-specific parameters.
            
        Returns:
            ToolResult with success/failure and data.
        """
        pass
    
    def validate_params(self, **kwargs: Any) -> bool:
        """
        Validate parameters against the tool's schema.
        
        Args:
            **kwargs: Parameters to validate.
            
        Returns:
            True if all required parameters with no defaults are present.
        """
        for param in self._metadata.parameters:
            if param.required and param.name not in kwargs:
                if param.default is None:
                    return False
        return True
    
    def health_check(self) -> dict[str, Any]:
        """Return tool health status."""
        return {
            "tool": self.name,
            "version": self._metadata.version,
            "category": self._metadata.category.value,
            "status": "ok"
        }