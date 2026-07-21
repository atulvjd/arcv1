from __future__ import annotations

from abc import ABC, abstractmethod

from agents.base.message import Message


class AgentMessenger(ABC):

    @abstractmethod
    def receive(self, message: Message):
        ...