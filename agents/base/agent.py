"""
ArcV1 Base Agent
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import uuid4

from agents.base.context import AgentContext
from agents.base.message import Message
from agents.base.state import AgentState
from agents.base.task import Task
from core.logger import get_logger


class BaseAgent(ABC):
    """
    Base class for every ArcV1 agent.
    """

    def __init__(
        self,
        name: str,
        context: AgentContext,
    ) -> None:

        self.id = str(uuid4())
        self.name = name
        self.context = context

        self.logger = get_logger(name)

        self.state = AgentState.CREATED

    def initialize(self) -> None:
        self.logger.info("Initializing...")

        self.state = AgentState.INITIALIZING

        self.on_initialize()

        self.state = AgentState.READY

        self.logger.info("Ready")

    def start(self) -> None:
        if self.state == AgentState.CREATED:
            self.initialize()

        self.logger.info("Starting...")

        self.state = AgentState.RUNNING

        self.on_start()

    def stop(self) -> None:
        self.logger.info("Stopping...")

        self.on_stop()

        self.state = AgentState.STOPPED

    def execute(self, task: Task):
        self.logger.info(f"Executing task: {task.name}")

        return self.on_execute(task)

    def receive(self, message: Message):
        self.logger.info(
            f"Received event '{message.event}' from {message.sender}"
        )

        return self.on_message(message)

    @abstractmethod
    def on_initialize(self):
        pass

    @abstractmethod
    def on_start(self):
        pass

    @abstractmethod
    def on_stop(self):
        pass

    @abstractmethod
    def on_execute(self, task: Task):
        pass

    @abstractmethod
    def on_message(self, message: Message):
        pass