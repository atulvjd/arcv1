from __future__ import annotations

from abc import ABC, abstractmethod

from agents.base.task import Task


class AgentExecutor(ABC):

    @abstractmethod
    def execute(self, task: Task):
        ...