from __future__ import annotations

from services.base import BaseService


class MemoryService(BaseService):

    def __init__(self):

        super().__init__("MemoryService")

        self._memory = {}

    def remember(self, key, value):

        self._memory[key] = value

    def recall(self, key):

        return self._memory.get(key)

    def clear(self):

        self._memory.clear()