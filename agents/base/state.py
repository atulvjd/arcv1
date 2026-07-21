from __future__ import annotations

from enum import Enum, auto


class AgentState(Enum):
    CREATED = auto()
    INITIALIZING = auto()
    READY = auto()
    RUNNING = auto()
    PAUSED = auto()
    STOPPED = auto()
    ERROR = auto()