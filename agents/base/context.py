"""

ArcV1 Agent Context
"""

from __future__ import annotations

from dataclasses import dataclass

from core.config import Config
from core.events import EventBus
from core.logger import get_logger
from core.registry_manager import RegistryManager


@dataclass(slots=True)
class AgentContext:
    """
    Shared runtime context available to every agent.
    
    Provides access to all runtime components.
    """

    config: Config
    registry_manager: RegistryManager
    events: EventBus
    
    @property
    def registry(self):
        """Legacy accessor for backward compatibility."""
        return self.registry_manager.services
