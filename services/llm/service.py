from __future__ import annotations

from services.base import BaseService


class LLMService(BaseService):

    def __init__(self):

        super().__init__("LLMService")

        self.model = None

    def load(self, model):

        self.model = model

    def generate(self, prompt: str):

        if self.model is None:

            return "No model loaded."

        return self.model.generate(prompt)