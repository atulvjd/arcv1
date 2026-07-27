"""
ArcV1 Tool Service

Manages tool registration, retrieval, and execution.
Tools provide extended capabilities to agents.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any

from services.base import BaseService

# Import canonical tool definitions from tools/ layer
from tools.base import (
    BaseTool,
    ToolCategory,
    ToolMetadata,
    ToolParameter,
    ToolResult,
)


class MockTool(BaseTool):
    """
    Mock tool for testing purposes.

    Returns a predictable response based on input.
    Maintains backward compatibility with dict return type.
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

    def execute(self, **kwargs: Any) -> ToolResult:
        """
        Execute mock tool.

        Args:
            **kwargs: Ignored parameters.

        Returns:
            ToolResult with execution data.
        """
        self._execution_count += 1
        return ToolResult.ok(
            data={
                "tool": self.name,
                "execution_count": self._execution_count,
                "params": kwargs
            }
        )


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

        # Unwrap ToolResult if needed
        if isinstance(result, ToolResult):
            return result.data
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
