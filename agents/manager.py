"""
ArcV1 Agent Manager
"""

from __future__ import annotations

from agents.base.agent import BaseAgent
from agents.base.message import Message
from agents.base.task import Task


class AgentManager:

    def __init__(self):
        self._agents: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        if agent.name in self._agents:
            raise ValueError(f"Agent '{agent.name}' already exists.")

        self._agents[agent.name] = agent

    def unregister(self, name: str) -> None:
        self._agents.pop(name, None)

    def get(self, name: str) -> BaseAgent | None:
        return self._agents.get(name)

    def exists(self, name: str) -> bool:
        return name in self._agents

    def list(self) -> list[str]:
        return list(self._agents.keys())

    def count(self) -> int:
        return len(self._agents)

    def start_all(self):
        for agent in self._agents.values():
            agent.start()

    def stop_all(self):
        for agent in self._agents.values():
            agent.stop()

    def broadcast(self, message: Message):
        for agent in self._agents.values():
            agent.receive(message)

    def execute(self, agent_name: str, task: Task):
        agent = self.get(agent_name)

        if agent is None:
            raise ValueError(f"Agent '{agent_name}' not found.")

        return agent.execute(task)