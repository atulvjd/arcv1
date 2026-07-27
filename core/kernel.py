"""
ArcV1 Kernel

Responsible for bootstrapping and shutting down the ArcV1 runtime.
Coordinates all components including the Execution Layer.
Internal state. External orchestration.
"""

from __future__ import annotations

from agents.manager import AgentManager
from core.config import Config
from core.events import EventBus
from core.logger import get_logger
from core.messaging.bus import MessageBus
from core.messaging.router import MessageRouter
from core.permissions.system import PermissionSystem
from core.queue import TaskQueue
from core.registry_manager import RegistryManager
from core.scheduler.scheduler import Scheduler
from core.scheduler.hooks import LoggingHook
from core.state import RuntimeState, StateManager
from models.base import ModelConfig
from models.manager import ModelManager
from models.registry import ModelRegistry
from models.providers import MockProvider
from services.base import BaseService
from services.llm import LLMService
from services.memory import MemoryService
from services.prompt import PromptService
from services.router import RouterService
from services.tool import ToolService
from tools.filesystem.tool import FilesystemTool
from tools.terminal.tool import TerminalTool


class Kernel:
    """Core runtime kernel for ArcV1."""

    def __init__(self) -> None:
        self.logger = get_logger("Kernel")

        # Core Services
        self.config = Config()
        self.events = EventBus()

        # Registry Manager
        self.registry = RegistryManager()

        # State Management
        self.state = StateManager()

        # Agent Manager
        self.agent_manager = AgentManager()

        # Messaging Layer
        self.message_bus = MessageBus()
        self.message_router = MessageRouter(self.message_bus)

        # Task Queue & Scheduler
        self.task_queue = TaskQueue()
        self.scheduler = Scheduler(
            queue=self.task_queue,
            agent_manager=self.agent_manager,
            event_bus=self.events,
            state_manager=self.state
        )
        self.scheduler.add_hook(LoggingHook())

        # Permission System
        self.permissions = PermissionSystem()
        self.permissions.setup_default_policies()

        # Model Layer
        self.model_registry = ModelRegistry()
        self.model_manager = ModelManager(registry=self.model_registry)

        # ArcV1 Services
        self.services: dict[str, BaseService] = {
            "llm": LLMService(),
            "memory": MemoryService(),
            "prompt": PromptService(),
            "router": RouterService(),
            "tool": ToolService(),
        }

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
        self.state.set_runtime_state(RuntimeState.BOOTING)

        # Register core infrastructure
        self.registry.services.register("config", self.config)
        self.registry.services.register("logger", self.logger)
        self.registry.services.register("events", self.events)
        self.registry.services.register("state", self.state)
        self.registry.services.register("agent_manager", self.agent_manager)
        self.registry.services.register("message_bus", self.message_bus)
        self.registry.services.register("message_router", self.message_router)
        self.registry.services.register("task_queue", self.task_queue)
        self.registry.services.register("permissions", self.permissions)
        self.registry.services.register("scheduler", self.scheduler)
        self.registry.services.register("model_manager", self.model_manager)
        self.registry.services.register("model_registry", self.model_registry)

        # Register default tools before services start
        self._register_default_tools()

        # Initialize and start services
        for name, service in self.services.items():
            self.logger.info(f"Initializing service: {name}")
            service.initialize()
            service.start()
            self.registry.services.register(f"service_{name}", service)

            # Connect LLMService to ModelManager
            if isinstance(service, LLMService):
                service.set_model_manager(self.model_manager)

        # Load default model provider
        self._load_default_model()

        # Register default agents in registry
        self.registry.agents.register("scheduler", self.scheduler)

        # Register state components
        self.state.register_component("kernel")
        self.state.register_component("scheduler")
        self.state.register_component("message_bus")
        self.state.register_component("model_manager")
        self.state.register_component("permissions")

        # Start scheduler
        self.scheduler.start()

        # Notify subscribers
        self.events.emit("kernel.boot")

        # Start all agents
        self.agent_manager.start_all()

        self._running = True
        self.state.set_runtime_state(RuntimeState.RUNNING)
        self.state.update_health("kernel", "running")

        self.logger.info("Kernel started successfully.")

    def _register_default_tools(self) -> None:
        """Register default tools into ToolService."""
        tool_service = self.services["tool"]

        allowed_paths = self.config.get("tools.filesystem.allowed_paths", None)
        fs_tool = FilesystemTool(allowed_paths=allowed_paths)
        tool_service.register(fs_tool)
        self.registry.tools.register("filesystem", fs_tool)
        self.logger.info("Registered FilesystemTool.")

        allowed_commands = self.config.get("tools.terminal.allowed_commands", None)
        term_tool = TerminalTool(allowed_commands=allowed_commands)
        tool_service.register(term_tool)
        self.registry.tools.register("terminal", term_tool)
        self.logger.info("Registered TerminalTool.")

    def _load_default_model(self) -> None:
        """Load the default model provider."""
        mock_provider = MockProvider()
        self.model_registry.register("mock", mock_provider)

        mock_config = ModelConfig(
            model_id=self.config.get("models.default.model_id", "mock-default"),
            endpoint=self.config.get("models.default.endpoint", ""),
            api_key=self.config.get("models.default.api_key", ""),
            parameters=self.config.get("models.default.parameters", {})
        )
        self.model_manager.load_model("mock", mock_config)

        self.registry.models.register("mock", mock_provider)
        self.logger.info(f"Loaded default model: mock ({mock_config.model_id})")

    def shutdown(self) -> None:
        """Shutdown the ArcV1 kernel."""

        if not self._running:
            self.logger.warning("Kernel is already stopped.")
            return

        self.logger.info("Shutting down ArcV1 Kernel...")
        self.state.set_runtime_state(RuntimeState.SHUTTING_DOWN)

        self.events.emit("kernel.shutdown")

        self.model_manager.unload_model()

        self.scheduler.stop()

        self.agent_manager.stop_all()

        for name in reversed(list(self.services.keys())):
            self.logger.info(f"Stopping service: {name}")
            self.services[name].stop()

        self.registry.services.clear()
        self.registry.agents.clear()
        self.registry.tools.clear()
        self.registry.models.clear()
        self.registry.plugins.clear()

        self.state.clear()

        self._running = False

        self.logger.info("Kernel stopped successfully.")

    def get_service(self, name: str) -> BaseService | None:
        """
        Get a service by name.

        Args:
            name: Service name (e.g., 'llm', 'memory').

        Returns:
            The service if found, None otherwise.
        """
        return self.services.get(name)

    def health_check(self) -> dict:
        """
        Return comprehensive health check for all components.

        Returns:
            Dict with health status of all subsystems.
        """
        return {
            "kernel": {
                "running": self._running,
                "state": self.state.runtime_state.name,
            },
            "services": {
                name: service.health_check()
                for name, service in self.services.items()
            },
            "messaging": self.message_bus.health_check(),
            "model_manager": self.model_manager.health_check(),
            "scheduler": self.scheduler.health_check(),
            "permissions": self.permissions.health_check(),
            "state": self.state.snapshot(),
        }
