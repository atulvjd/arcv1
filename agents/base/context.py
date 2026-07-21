"""
ArcV1 Agent Context
"""

from __future__ import annotations

from dataclasses import dataclass

from core.config import Config
from core.events import EventBus
from core.logger import get_logger
from core.registry import Registry


@dataclass(slots=True)
class AgentContext:
    """
    Shared runtime context available to every agent.
    """

    config: Config
    registry: Registry
    events: EventBus