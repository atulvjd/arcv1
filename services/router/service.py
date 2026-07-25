"""
ArcV1 Kernel

Responsible for bootstrapping and shutting down the ArcV1 runtime.
"""

from __future__ import annotations

from agents.manager import AgentManager
from core.config import Config
from core.events import EventBus
from core.logger import get_logger
from core.registry_manager import RegistryManager


class Kernel:
    """Core runtime kernel."""

    def __init__(self) -> None:
        self.logger = get_logger("Kernel")

        # Core Services
        self.config = Config()
        self.events = EventBus()

        # Registry Manager
        self.registry = RegistryManager()

        # Agent Manager
        self.agent_manager = AgentManager()

        self._running = False

    @property
    def running(self) -> bool:
        """Return True if the kernel is running."""
        return self._running

    def boot(self) -> None:
        """Boot the ArcV1 kernel."""

        if self._running:
            self.logger.warning("Kernel is already running.")
            return

        self.logger.info("Booting ArcV1 Kernel...")

        # Register core services
        self.registry.services.register("config", self.config)
        self.registry.services.register("logger", self.logger)
        self.registry.services.register("events", self.events)
        self.registry.services.register("agent_manager", self.agent_manager)

        # Notify subscribers
        self.events.emit("kernel.boot")

        # Start all agents
        self.agent_manager.start_all()

        self._running = True

        self.logger.info("Kernel started successfully.")

    def shutdown(self) -> None:
        """Shutdown the ArcV1 kernel."""

        if not self._running:
            self.logger.warning("Kernel is already stopped.")
            return

        self.logger.info("Shutting down ArcV1 Kernel...")

        # Notify subscribers
        self.events.emit("kernel.shutdown")

        # Stop all agents
        self.agent_manager.stop_all()

        # Clear registries
        self.registry.services.clear()
        self.registry.agents.clear()
        self.registry.tools.clear()
        self.registry.models.clear()
        self.registry.plugins.clear()

        self._running = False

        self.logger.info("Kernel stopped successfully.")