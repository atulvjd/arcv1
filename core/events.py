"""
ArcV1 Event Bus
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Any


class EventBus:
    """Simple publish/subscribe event system."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[..., None]]] = defaultdict(list)

    def subscribe(self, event: str, callback: Callable[..., None]) -> None:
        """Register a callback for an event."""
        self._subscribers[event].append(callback)

    def unsubscribe(self, event: str, callback: Callable[..., None]) -> None:
        """Remove a callback from an event."""
        if event in self._subscribers:
            self._subscribers[event].remove(callback)

    def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        """Emit an event to all subscribers."""
        for callback in self._subscribers.get(event, []):
            callback(*args, **kwargs)

    def clear(self) -> None:
        """Remove all event subscriptions."""
        self._subscribers.clear()