"""
ArcV1 Registry

Stores and manages all runtime components.
"""

from __future__ import annotations

from typing import Any


class Registry:
    """Central registry for ArcV1."""

    def __init__(self) -> None:
        self._items: dict[str, Any] = {}

    def register(self, name: str, obj: Any) -> None:
        if name in self._items:
            raise ValueError(f"'{name}' is already registered.")
        self._items[name] = obj

    def unregister(self, name: str) -> None:
        if name not in self._items:
            raise KeyError(f"'{name}' is not registered.")
        del self._items[name]

    def get(self, name: str) -> Any:
        if name not in self._items:
            raise KeyError(f"'{name}' is not registered.")
        return self._items[name]

    def exists(self, name: str) -> bool:
        return name in self._items

    def list(self) -> list[str]:
        return sorted(self._items.keys())

    def clear(self) -> None:
        self._items.clear()

    def count(self) -> int:
        return len(self._items)