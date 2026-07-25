from __future__ import annotations

from services.base import BaseService


class PromptService(BaseService):

    def __init__(self):

        super().__init__("PromptService")

        self._prompts = {}

    def register(self, name, prompt):

        self._prompts[name] = prompt

    def get(self, name):

        return self._prompts.get(name)