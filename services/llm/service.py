"""
ArcV1 LLM Service

Provides abstraction for language model operations.
Communicates with models through the Model Layer (BaseModel).
Supports backend pattern for backward compatibility.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Optional

from models.base import BaseModel, ModelConfig, ModelResult
from models.manager import ModelManager
from services.base import BaseService


class BaseLLMBackend(ABC):
    """
    Abstract interface for LLM backends.

    Deprecated: Use BaseModel from models.base instead.
    Kept for backward compatibility.
    """

    def __init__(self, name: str, config: dict[str, Any] | None = None) -> None:
        self.name = name
        self.config = config or {}

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> str:
        pass

    @abstractmethod
    async def generate_stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        pass

    def health_check(self) -> dict[str, Any]:
        return {"backend": self.name, "status": "ok"}


class MockLLMBackend(BaseLLMBackend):
    """
    Mock LLM backend for testing.

    Deprecated: Use MockProvider from models.providers instead.
    """

    def __init__(self, name: str = "mock", config: dict[str, Any] | None = None) -> None:
        super().__init__(name, config)
        self._call_count = 0

    def generate(self, prompt: str, **kwargs: Any) -> str:
        self._call_count += 1
        return f"[MockLLM] Response to: {prompt[:50]}..."

    async def generate_stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        response = self.generate(prompt, **kwargs)
        words = response.split(" ")
        for word in words:
            yield word + " "

    @property
    def call_count(self) -> int:
        return self._call_count


class LLMService(BaseService):
    """
    Service for managing language model operations.

    Provides a unified interface for text generation.
    Communicates with models through the Model Layer.
    Supports both ModelLayer and legacy Backend pattern.
    """

    def __init__(self, name: str = "LLMService") -> None:
        super().__init__(name)
        self._backend: BaseLLMBackend | None = None
        self._model_manager: ModelManager | None = None
        self._default_params: dict[str, Any] = {}

    def on_initialize(self) -> None:
        self._default_params = self._config.get("default_params", {})
        self.logger.debug(f"Default params: {self._default_params}")

    def on_start(self) -> None:
        if self._model_manager is None and self._backend is None:
            self.logger.warning("No model layer or backend configured.")
        else:
            source = "ModelLayer" if self._model_manager else "Backend"
            self.logger.info(f"Using {source} for generation.")

    def on_stop(self) -> None:
        self.logger.info("LLM service stopped.")

    def set_model_manager(self, manager: ModelManager) -> None:
        """
        Set the ModelManager for Model Layer integration.

        Args:
            manager: ModelManager instance with loaded models.
        """
        self._model_manager = manager
        self.logger.info("ModelManager connected.")

    def load_backend(self, backend: BaseLLMBackend) -> None:
        """Load a legacy backend (backward compatible)."""
        self._backend = backend
        self.logger.info(f"Loaded backend: {backend.name}")

    def unload_backend(self) -> None:
        """Unload the current backend."""
        self._backend = None
        self.logger.info("Backend unloaded.")

    @property
    def backend(self) -> BaseLLMBackend | None:
        return self._backend

    @property
    def model_manager(self) -> ModelManager | None:
        return self._model_manager

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """
        Generate text using the active model provider.

        Precedence:
        1. Model Layer (recommended)
        2. Legacy Backend (deprecated)

        Args:
            prompt: Input prompt.
            **kwargs: Generation parameters.

        Returns:
            Generated text string.
        """
        params = {**self._default_params, **kwargs}

        if self._model_manager and self._model_manager.active_model:
            result = self._model_manager.generate(prompt, **params)
            return result.text

        if self._backend:
            return self._backend.generate(prompt, **params)

        raise RuntimeError("No LLM provider available. Configure a model or backend.")

    async def generate_stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        """
        Stream generated text from the active provider.

        Args:
            prompt: Input prompt.
            **kwargs: Generation parameters.

        Yields:
            Text chunks.
        """
        params = {**self._default_params, **kwargs}

        if self._model_manager and self._model_manager.active_model:
            async for chunk in self._model_manager.stream(prompt, **params):
                yield chunk.text
            return

        if self._backend:
            async for chunk in self._backend.generate_stream(prompt, **params):
                yield chunk
            return

        raise RuntimeError("No LLM provider available.")

    def health_check(self) -> dict[str, Any]:
        """Return health check information."""
        base_health = super().health_check()

        if self._model_manager and self._model_manager.active_model:
            base_health["provider"] = "model_layer"
            base_health["active_model"] = self._model_manager.active_model_name
            base_health["model_health"] = self._model_manager.health_check()
        elif self._backend:
            base_health["provider"] = "legacy_backend"
            base_health["backend"] = self._backend.health_check()
        else:
            base_health["provider"] = None

        return base_health
