"""
ArcV1 Model Registry

Specialized registry for model provider instances.
Integrates with the core Registry pattern.
"""

from __future__ import annotations

from typing import Any

from models.base import BaseModel


class ModelRegistry:
    """
    Registry for model instances.
    
    Stores and retrieves model providers by name.
    Supports multiple models with different providers.
    """
    
    def __init__(self) -> None:
        """Initialize an empty model registry."""
        self._models: dict[str, BaseModel] = {}
    
    def register(self, name: str, model: BaseModel) -> None:
        """
        Register a model instance.
        
        Args:
            name: Unique name for this model.
            model: Model instance.
            
        Raises:
            ValueError: If name already registered.
        """
        if name in self._models:
            raise ValueError(f"Model '{name}' is already registered.")
        self._models[name] = model
    
    def unregister(self, name: str) -> None:
        """
        Unregister a model.
        
        Args:
            name: Name of the model to remove.
            
        Raises:
            KeyError: If model not found.
        """
        if name not in self._models:
            raise KeyError(f"Model '{name}' not found.")
        del self._models[name]
    
    def get(self, name: str) -> BaseModel | None:
        """
        Get a model by name.
        
        Args:
            name: Model name.
            
        Returns:
            The model if found, None otherwise.
        """
        return self._models.get(name)
    
    def list(self) -> list[str]:
        """
        List all registered model names.
        
        Returns:
            Sorted list of model names.
        """
        return sorted(self._models.keys())
    
    def list_loaded(self) -> list[str]:
        """
        List all currently loaded model names.
        
        Returns:
            List of loaded model names.
        """
        return [
            name for name, model in self._models.items()
            if model.loaded
        ]
    
    def exists(self, name: str) -> bool:
        """
        Check if a model is registered.
        
        Args:
            name: Model name.
            
        Returns:
            True if registered.
        """
        return name in self._models
    
    def count(self) -> int:
        """Return the number of registered models."""
        return len(self._models)
    
    def clear(self) -> None:
        """Unload and remove all models."""
        for model in self._models.values():
            if model.loaded:
                model.unload()
        self._models.clear()