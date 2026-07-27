"""
ArcV1 State Management

Provides state tracking and persistence for the runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any


class RuntimeState(Enum):
    """Top-level runtime states."""
    STOPPED = auto()
    BOOTING = auto()
    RUNNING = auto()
    DEGRADED = auto()
    SHUTTING_DOWN = auto()
    ERROR = auto()


@dataclass
class ComponentHealth:
    """Health status of a runtime component."""
    name: str
    status: str = "unknown"
    last_heartbeat: datetime = field(default_factory=datetime.now)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class StateManager:
    """Manages runtime state and component health."""
    
    def __init__(self) -> None:
        self._runtime_state = RuntimeState.STOPPED
        self._component_health: dict[str, ComponentHealth] = {}
    
    @property
    def runtime_state(self) -> RuntimeState:
        return self._runtime_state
    
    def set_runtime_state(self, state: RuntimeState) -> None:
        self._runtime_state = state
    
    def register_component(self, name: str) -> None:
        self._component_health[name] = ComponentHealth(name=name)
    
    def update_health(self, name: str, status: str, **metadata: Any) -> None:
        if name in self._component_health:
            self._component_health[name].status = status
            self._component_health[name].last_heartbeat = datetime.now()
            self._component_health[name].metadata.update(metadata)
    
    def record_error(self, name: str, error: str) -> None:
        if name in self._component_health:
            self._component_health[name].errors.append(error)
            self._component_health[name].status = "error"
    
    def get_health(self, name: str) -> ComponentHealth | None:
        return self._component_health.get(name)
    
    def all_healthy(self) -> bool:
        return all(
            h.status == "ok" or h.status == "running"
            for h in self._component_health.values()
        )
    
    def snapshot(self) -> dict[str, Any]:
        """Return a complete state snapshot."""
        return {
            "runtime_state": self._runtime_state.name,
            "components": {
                name: {
                    "status": health.status,
                    "last_heartbeat": health.last_heartbeat.isoformat(),
                    "error_count": len(health.errors),
                    "metadata": health.metadata
                }
                for name, health in self._component_health.items()
            },
            "all_healthy": self.all_healthy()
        }
    
    def clear(self) -> None:
        self._runtime_state = RuntimeState.STOPPED
        self._component_health.clear()