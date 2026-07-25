"""
ArcV1 LLM Service

Provides abstraction for language model operations.
Models are loaded dynamically and can be replaced at runtime.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Optional

from services.base import BaseService


class BaseLLMBackend(ABC):
    """
    Abstract interface for LLM backends.
    
    Implementations should provide concrete logic for text generation.
    """
    
    def __init__(self, name: str, config: dict[str, Any] | None = None) -> None:
        """
        Initialize the backend.
        
        Args:
            name: Name of the backend.
            config: Optional configuration parameters.
        """
        self.name = name
        self.config = config or {}
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """
        Generate text from a prompt.
        
        Args:
            prompt: The input prompt string.
            **kwargs: Additional generation parameters.
            
        Returns:
            Generated text string.
        """
        pass
    
    @abstractmethod
    async def generate_stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        """
        Stream generated text tokens.
        
        Args:
            prompt: The input prompt string.
            **kwargs: Additional generation parameters.
            
        Returns:
            Async iterator of text chunks.
        """
        pass
    
    def health_check(self) -> dict[str, Any]:
        """
        Check backend health.
        
        Returns:
            Dictionary with health status.
        """
        return {"backend": self.name, "status": "ok"}


class MockLLMBackend(BaseLLMBackend):
    """
    Mock LLM backend for testing and development.
    
    Returns placeholder responses without actual model inference.
    """
    
    def __init__(self, name: str = "mock", config: dict[str, Any] | None = None) -> None:
        """
        Initialize mock backend.
        
        Args:
            name: Backend name.
            config: Optional configuration.
        """
        super().__init__(name, config)
        self._call_count = 0
    
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """
        Generate mock response.
        
        Args:
            prompt: Input prompt.
            **kwargs: Ignored parameters.
            
        Returns:
            Placeholder response string.
        """
        self._call_count += 1
        return f"[MockLLM] Response to: {prompt[:50]}..."
    
    async def generate_stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        """
        Stream mock response tokens.
        
        Args:
            prompt: Input prompt.
            **kwargs: Ignored parameters.
            
        Yields:
            Mock response chunks.
        """
        response = self.generate(prompt, **kwargs)
        words = response.split(" ")
        for word in words:
            yield word + " "
    
    @property
    def call_count(self) -> int:
        """Return number of generate calls made."""
        return self._call_count


class LLMService(BaseService):
    """
    Service for managing language model operations.
    
    Provides a unified interface for text generation while allowing
    the underlying backend to be swapped at runtime.
    """
    
    def __init__(self, name: str = "LLMService") -> None:
        """
        Initialize the LLM service.
        
        Args:
            name: Service name.
        """
        super().__init__(name)
        self._backend: BaseLLMBackend | None = None
        self._default_params: dict[str, Any] = {}
    
    def on_initialize(self) -> None:
        """
        Initialize service state.
        
        Loads default parameters from configuration if available.
        """
        self._default_params = self._config.get("default_params", {})
        self.logger.debug(f"Default params: {self._default_params}")
    
    def on_start(self) -> None:
        """
        Start the service.
        
        Verifies that a backend is loaded and healthy.
        """
        if self._backend is None:
            self.logger.warning("No LLM backend loaded. Service running in offline mode.")
        else:
            self.logger.info(f"LLM backend '{self._backend.name}' is active.")
    
    def on_stop(self) -> None:
        """
        Stop the service.
        
        Cleans up resources but preserves the loaded backend.
        """
        self.logger.info("LLM service stopped. Backend retained.")
    
    def load_backend(self, backend: BaseLLMBackend) -> None:
        """
        Load or replace the current LLM backend.
        
        Args:
            backend: The backend implementation to use.
        """
        self._backend = backend
        self.logger.info(f"Loaded backend: {backend.name}")
    
    def unload_backend(self) -> None:
        """
        Unload the current backend.
        
        Sets the active backend to None.
        """
        self._backend = None
        self.logger.info("Backend unloaded.")
    
    @property
    def backend(self) -> BaseLLMBackend | None:
        """Return the currently loaded backend."""
        return self._backend
    
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """
        Generate text using the loaded backend.
        
        Args:
            prompt: The input prompt.
            **kwargs: Generation parameters (merged with defaults).
            
        Returns:
            Generated text string.
            
        Raises:
            RuntimeError: If no backend is loaded.
        """
        if self._backend is None:
            raise RuntimeError("No LLM backend loaded.")
        
        params = {**self._default_params, **kwargs}
        return self._backend.generate(prompt, **params)
    
    async def generate_stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        """
        Stream generated text from the loaded backend.
        
        Args:
            prompt: The input prompt.
            **kwargs: Generation parameters.
            
        Returns:
            Async iterator of text chunks.
            
        Raises:
            RuntimeError: If no backend is loaded.
        """
        if self._backend is None:
            raise RuntimeError("No LLM backend loaded.")
        
        params = {**self._default_params, **kwargs}
        async for chunk in self._backend.generate_stream(prompt, **params):
            yield chunk
    
    def health_check(self) -> dict[str, Any]:
        """
        Perform health check including backend status.
        
        Returns:
            Dictionary with service and backend health info.
        """
        base_health = super().health_check()
        if self._backend:
            base_health["backend"] = self._backend.health_check()
        else:
            base_health["backend"] = None
        return base_health
