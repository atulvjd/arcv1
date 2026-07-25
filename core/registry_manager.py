"""
ArcV1 Registry Manager

Holds all typed registries used by ArcV1.
"""

from __future__ import annotations

from core.registry import Registry


class RegistryManager:
    """Container for all ArcV1 registries."""

    def __init__(self, name: str = "registry") -> None:
        self.name = name
        self._items: dict[str, object] = {}
        self.services = Registry("services")
        self.agents = Registry("agents")
        self.tools = Registry("tools")
        self.models = Registry("models")
        self.plugins = Registry("plugins")