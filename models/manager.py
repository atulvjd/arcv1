"""
ArcV1 Model Manager

Manages model lifecycle: loading, unloading, and switching.
Coordinates with ModelRegistry for model storage.
"""

from __future__ import annotations

from typing import Any, AsyncIterator

from core.exceptions import ModelError
from core.logger import get_logger
from models.base import (
    BaseModel,
    ModelConfig,
    ModelMetadata,
    ModelResult,
    ModelStreamChunk,
)
from models.registry import ModelRegistry


class ModelManager:
    """
    Manages model lifecycle and operations.
    
    Responsibilities:
    - Load/unload models
    - Track active model
    - Delegate generate/stream to active model
    - Coordinate with ModelRegistry
    """
    
    def __init__(self, registry: ModelRegistry | None = None) -> None:
        """
        Initialize the model manager.
        
        Args:
            registry: Optional ModelRegistry instance.
                     Creates one if not provided.
        """
        self.logger = get_logger("ModelManager")
        self._registry = registry or ModelRegistry()
        self._active_model_name: str | None = None
    
    @property
    def registry(self) -> ModelRegistry:
        """Return the underlying model registry."""
        return self._registry
    
    @property
    def active_model_name(self) -> str | None:
        """Return the name of the currently active model."""
        return self._active_model_name
    
    @property
    def active_model(self) -> BaseModel | None:
        """Return the currently active model instance."""
        if self._active_model_name is None:
            return None
        return self._registry.get(self._active_model_name)
    
    def register_model(self, name: str, model: BaseModel) -> None:
        """
        Register a model with the manager.
        
        Args:
            name: Unique name for this model.
            model: Model instance to register.
            
        Raises:
            ValueError: If name already registered.
        """
        self._registry.register(name, model)
        self.logger.debug(f"Registered model: {name}")
    
    def load_model(self, name: str, config: ModelConfig) -> BaseModel:
        """
        Load and optionally activate a model.
        
        If the model is not already registered, creates it
        from the provider registry.
        
        Args:
            name: Name of the model to load.
            config: Configuration for loading.
            
        Returns:
            The loaded BaseModel instance.
            
        Raises:
            ModelError: If loading fails.
        """
        model = self._registry.get(name)
        if model is None:
            raise ModelError(f"Model '{name}' is not registered.")
        
        try:
            model.load(config)
            self._active_model_name = name
            self.logger.info(f"Loaded model: {name} ({config.model_id})")
            return model
        except Exception as e:
            raise ModelError(f"Failed to load model '{name}': {e}") from e
    
    def unload_model(self, name: str | None = None) -> None:
        """
        Unload a specific model or the active model.
        
        Args:
            name: Name of the model to unload. If None, unloads active.
            
        Raises:
            KeyError: If model not found.
        """
        target = name or self._active_model_name
        if target is None:
            self.logger.warning("No model to unload.")
            return
        
        model = self._registry.get(target)
        if model is None:
            raise KeyError(f"Model '{target}' not found.")
        
        if model.loaded:
            model.unload()
            self.logger.info(f"Unloaded model: {target}")
        
        if target == self._active_model_name:
            self._active_model_name = None
    
    def switch_model(self, name: str) -> BaseModel:
        """
        Switch the active model without reloading.
        
        Args:
            name: Name of the model to make active.
            
        Returns:
            The new active model.
            
        Raises:
            KeyError: If model not found.
            ModelError: If model is not loaded.
        """
        model = self._registry.get(name)
        if model is None:
            raise KeyError(f"Model '{name}' not found.")
        if not model.loaded:
            raise ModelError(f"Model '{name}' is not loaded.")
        
        self._active_model_name = name
        self.logger.info(f"Switched to model: {name}")
        return model
    
    def generate(self, prompt: str, **kwargs: Any) -> ModelResult:
        """
        Generate text using the active model.
        
        Args:
            prompt: Input prompt.
            **kwargs: Additional generation parameters.
            
        Returns:
            ModelResult with generated text.
            
        Raises:
            RuntimeError: If no active model.
        """
        model = self.active_model
        if model is None:
            raise RuntimeError("No active model loaded.")
        return model.generate(prompt, **kwargs)
    
    async def stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[ModelStreamChunk]:
        """
        Stream text from the active model.
        
        Args:
            prompt: Input prompt.
            **kwargs: Additional parameters.
            
        Yields:
            ModelStreamChunks from the active model.
            
        Raises:
            RuntimeError: If no active model.
        """
        model = self.active_model
        if model is None:
            raise RuntimeError("No active model loaded.")
        async for chunk in model.stream(prompt, **kwargs):
            yield chunk
    
    def embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings using the active model.
        
        Args:
            texts: List of input texts.
            
        Returns:
            List of embedding vectors.
        """
        model = self.active_model
        if model is None:
            raise RuntimeError("No active model loaded.")
        return model.embeddings(texts)
    
    def active_metadata(self) -> ModelMetadata:
        """
        Return metadata for the active model.
        
        Returns:
            ModelMetadata.
            
        Raises:
            RuntimeError: If no active model.
        """
        model = self.active_model
        if model is None:
            raise RuntimeError("No active model loaded.")
        return model.metadata()
    
    def health_check(self) -> dict[str, Any]:
        """
        Perform health check on the model manager.
        
        Returns:
            Dictionary with health status.
        """
        active = self.active_model
        return {
            "active_model": self._active_model_name,
            "is_loaded": active is not None and active.loaded,
            "registered_models": self._registry.count(),
            "loaded_models": len(self._registry.list_loaded()),
        }