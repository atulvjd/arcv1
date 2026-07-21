"""
ArcV1 Kernel

Responsible for bootstrapping and shutting down the ArcV1 runtime.
"""

from __future__ import annotations

from core.config import Config
from core.events import EventBus
from core.logger import get_logger
from core.registry import Registry
from agents.manager import AgentManager

class Kernel:
    """Core runtime kernel."""

    def __init__(self) -> None:
        self.logger = get_logger("Kernel")
        self.config = Config()
        self.events = EventBus()
        self.registry = Registry()
        self.agent_manager = AgentManager()

        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    def boot(self) -> None:
        """Start the kernel."""

        if self._running:
            self.logger.warning("Kernel is already running.")
            return

        self.logger.info("Booting ArcV1 Kernel...")

        self.registry.register("config", self.config)
        self.registry.register("logger", self.logger)
        self.registry.register("events", self.events)
        self.registry.register("agent_manager", self.agent_manager)
        self.events.emit("kernel.boot")


        self._running = True
        self.agent_manager.start_all()
        self.logger.info("Kernel started successfully.")

    def shutdown(self) -> None:
        """Stop the kernel."""

        if not self._running:
            self.logger.warning("Kernel is already stopped.")
            return

        self.logger.info("Shutting down ArcV1 Kernel...")

        self.events.emit("kernel.shutdown")

        self.registry.clear()

        self._running = False

        self.logger.info("Kernel stopped successfully.")
        self.agent_manager.stop_all()