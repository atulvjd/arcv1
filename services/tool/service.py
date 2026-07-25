from __future__ import annotations

from services.base import BaseService


class ToolService(BaseService):

    def __init__(self):

        super().__init__("ToolService")

        self._tools = {}

    def register(self, name, tool):

        self._tools[name] = tool

    def get(self, name):

        return self._tools.get(name)

    def list(self):

        return list(self._tools.keys())