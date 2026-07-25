"""
ArcV1 Tool Service

Manages tool registration, retrieval, and execution.
Tools provide extended capabilities to agents.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

from services.base import BaseService


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
        type_name: Type of the parameter (e.g., 'str', 'int', 'bool').
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
        parameters: List of tool parameters.
        version: Tool version.
        author: Tool author.
    """
    name: str
    description: str = ""
    category: ToolCategory = ToolCategory.CUSTOM
    parameters: list[ToolParameter] = field(default_factory=list)
    version: str = "1.0.0"
    author: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "parameters": [p.to_dict() for p in self.parameters],
            "version": self.version,
            "author": self.author
        }


class BaseTool(ABC):
    """
    Abstract base class for all tools.
    
    Tools must implement the execute method and provide metadata.
    """
    
    def __init__(self, metadata: ToolMetadata) -> None:
        """
        Initialize the tool.
        
        Args:
            metadata: Tool metadata describing its capabilities.
        """
        self.metadata = metadata
    
    @property
    def name(self) -> str:
        """Return tool name."""
        return self.metadata.name
    
    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        """
        Execute the tool with the given parameters.
        
        Args:
            **kwargs: Tool-specific parameters.
            
        Returns:
            Tool execution result.
        """
        pass
    
    def validate_params(self, **kwargs: Any) -> bool:
        """
        Validate provided parameters against tool schema.
        
        Args:
            **kwargs: Parameters to validate.
            
        Returns:
            True if parameters are valid.
        """
        for param in self.metadata.parameters:
            if param.required and param.name not in kwargs:
                if param.default is None:
                    return False
        return True
    
    def health_check(self) -> dict[str, Any]:
        """
        Check tool health.
        
        Returns:
            Dictionary with health status.
        """
        return {
            "tool": self.name,
            "version": self.metadata.version,
            "category": self.metadata.category.value,
            "status": "ok"
        }


class MockTool(BaseTool):
    """
    Mock tool for testing purposes.
    
    Returns a predictable response based on input.
    """
    
    def __init__(self, name: str = "mock_tool", description: str = "A mock tool for testing") -> None:
        """
        Initialize mock tool.
        
        Args:
            name: Tool name.
            description: Tool description.
        """
        metadata = ToolMetadata(
            name=name,
            description=description,
            category=ToolCategory.CUSTOM
        )
        super().__init__(metadata)
        self._execution_count = 0
    
    def execute(self, **kwargs: Any) -> Any:
        """
        Execute mock tool.
        
        Args:
            **kwargs: Ignored parameters.
            
        Returns:
            Mock execution result.
        """
        self._execution_count += 1
        return {
            "tool": self.name,
            "execution_count": self._execution_count,
            "params": kwargs
        }


class ToolService(BaseService):
    """
    Service for managing tools.
    
    Provides registration, retrieval, and execution of tools
    that extend agent capabilities.
    """
    
    def __init__(self, name: str = "ToolService") -> None:
        """
        Initialize the tool service.
        
        Args:
            name: Service name.
        """
        super().__init__(name)
        self._tools: dict[str, BaseTool] = {}
    
    def on_initialize(self) -> None:
        """
        Initialize the tool service.
        
        Loads any configured tools.
        """
        self.logger.info("Tool service initialized.")
    
    def on_start(self) -> None:
        """Start the tool service."""
        self.logger.info(f"Tool service started with {len(self._tools)} tools.")
    
    def on_stop(self) -> None:
        """Stop the tool service."""
        self.logger.info("Tool service stopped.")
    
    def register(self, tool: BaseTool) -> None:
        """
        Register a tool.
        
        Args:
            tool: The tool to register.
            
        Raises:
            ValueError: If a tool with the same name already exists.
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered.")
        
        self._tools[tool.name] = tool
        self.logger.debug(f"Registered tool: {tool.name}")
    
    def unregister(self, name: str) -> None:
        """
        Unregister a tool.
        
        Args:
            name: Name of the tool to remove.
            
        Raises:
            KeyError: If tool not found.
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found.")
        
        del self._tools[name]
        self.logger.debug(f"Unregistered tool: {name}")
    
    def get(self, name: str) -> BaseTool | None:
        """
        Retrieve a tool by name.
        
        Args:
            name: Tool name.
            
        Returns:
            The tool if found, None otherwise.
        """
        return self._tools.get(name)
    
    def execute(self, name: str, **kwargs: Any) -> Any:
        """
        Execute a tool by name.
        
        Args:
            name: Tool name.
            **kwargs: Tool parameters.
            
        Returns:
            Tool execution result.
            
        Raises:
            KeyError: If tool not found.
            ValueError: If parameters are invalid.
        """
        tool = self.get(name)
        if tool is None:
            raise KeyError(f"Tool '{name}' not found.")
        
        if not tool.validate_params(**kwargs):
            raise ValueError(f"Invalid parameters for tool '{name}'.")
        
        self.logger.debug(f"Executing tool: {name}")
        result = tool.execute(**kwargs)
        self.logger.debug(f"Tool '{name}' executed successfully.")
        
        return result
    
    def list_tools(self) -> list[str]:
        """
        Return list of all registered tool names.
        
        Returns:
            Sorted list of tool names.
        """
        return sorted(self._tools.keys())
    
    def list_by_category(self, category: ToolCategory) -> list[str]:
        """
        Return list of tool names in a category.
        
        Args:
            category: The category to filter by.
            
        Returns:
            List of tool names in the category.
        """
        return [
            name for name, tool in self._tools.items()
            if tool.metadata.category == category
        ]
    
    def count(self) -> int:
        """Return number of registered tools."""
        return len(self._tools)
    
    def exists(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools
    
    def clear(self) -> None:
        """Remove all registered tools."""
        self._tools.clear()
        self.logger.info("All tools cleared.")
    
    def health_check(self) -> dict[str, Any]:
        """Perform health check."""
        base_health = super().health_check()
        base_health["tool_count"] = self.count()
        return base_health
