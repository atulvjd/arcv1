"""
ArcV1 Memory Service

Provides key-value memory storage with a replaceable backend.
Supports both in-memory and persistent storage implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from services.base import BaseService


class MemoryBackend(ABC):
    """
    Abstract interface for memory storage backends.
    
    Implementations can be in-memory, file-based, database, etc.
    """
    
    @abstractmethod
    def get(self, key: str) -> Any | None:
        """
        Retrieve a value by key.
        
        Args:
            key: The key to look up.
            
        Returns:
            The value if found, None otherwise.
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """
        Store a value with the given key.
        
        Args:
            key: The key to store under.
            value: The value to store.
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Delete a key-value pair.
        
        Args:
            key: The key to delete.
            
        Returns:
            True if key existed and was deleted, False otherwise.
        """
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Check if a key exists.
        
        Args:
            key: The key to check.
            
        Returns:
            True if key exists, False otherwise.
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """
        Clear all stored data.
        """
        pass
    
    @abstractmethod
    def keys(self) -> list[str]:
        """
        Return list of all stored keys.
        
        Returns:
            List of keys.
        """
        pass
    
    @abstractmethod
    def count(self) -> int:
        """
        Return number of stored items.
        
        Returns:
            Count of items.
        """
        pass
    
    def health_check(self) -> dict[str, Any]:
        """
        Check backend health.
        
        Returns:
            Dictionary with health status.
        """
        return {"backend": self.__class__.__name__, "count": self.count()}


class InMemoryBackend(MemoryBackend):
    """
    Simple in-memory storage backend.
    
    Data is lost when the process terminates.
    """
    
    def __init__(self) -> None:
        self._store: dict[str, Any] = {}
    
    def get(self, key: str) -> Any | None:
        return self._store.get(key)
    
    def set(self, key: str, value: Any) -> None:
        self._store[key] = value
    
    def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False
    
    def exists(self, key: str) -> bool:
        return key in self._store
    
    def clear(self) -> None:
        self._store.clear()
    
    def keys(self) -> list[str]:
        return list(self._store.keys())
    
    def count(self) -> int:
        return len(self._store)


class MemoryService(BaseService):
    """
    Service for managing agent and system memory.
    
    Provides a unified interface for key-value storage with
    support for different backend implementations.
    """
    
    def __init__(self, name: str = "MemoryService") -> None:
        """
        Initialize the memory service.
        
        Args:
            name: Service name.
        """
        super().__init__(name)
        self._backend: MemoryBackend | None = None
    
    def on_initialize(self) -> None:
        """
        Initialize the memory service.
        
        Loads the configured backend or defaults to InMemoryBackend.
        """
        # For now, we default to InMemoryBackend
        # In the future, we can load backend from config
        self._backend = InMemoryBackend()
        self.logger.info("Memory service initialized with InMemoryBackend.")
    
    def on_start(self) -> None:
        """
        Start the memory service.
        
        Verifies backend is available.
        """
        if self._backend is None:
            self.logger.warning("No memory backend loaded.")
        else:
            self.logger.info(f"Memory backend '{self._backend.__class__.__name__}' is active.")
    
    def on_stop(self) -> None:
        """
        Stop the memory service.
        
        Optionally persist data if backend supports it.
        """
        self.logger.info("Memory service stopped.")
    
    def load_backend(self, backend: MemoryBackend) -> None:
        """
        Load or replace the current memory backend.
        
        Args:
            backend: The backend implementation to use.
        """
        self._backend = backend
        self.logger.info(f"Loaded memory backend: {backend.__class__.__name__}")
    
    @property
    def backend(self) -> MemoryBackend | None:
        """Return the currently loaded backend."""
        return self._backend
    
    def remember(self, key: str, value: Any) -> None:
        """
        Store a value in memory.
        
        Args:
            key: The key to store under.
            value: The value to store.
            
        Raises:
            RuntimeError: If no backend is loaded.
        """
        if self._backend is None:
            raise RuntimeError("No memory backend loaded.")
        self._backend.set(key, value)
        self.logger.debug(f"Stored value for key: {key}")
    
    def recall(self, key: str) -> Any | None:
        """
        Retrieve a value from memory.
        
        Args:
            key: The key to look up.
            
        Returns:
            The value if found, None otherwise.
            
        Raises:
            RuntimeError: If no backend is loaded.
        """
        if self._backend is None:
            raise RuntimeError("No memory backend loaded.")
        return self._backend.get(key)
    
    def forget(self, key: str) -> bool:
        """
        Remove a value from memory.
        
        Args:
            key: The key to remove.
            
        Returns:
            True if key existed and was removed, False otherwise.
            
        Raises:
            RuntimeError: If no backend is loaded.
        """
        if self._backend is None:
            raise RuntimeError("No memory backend loaded.")
        return self._backend.delete(key)
    
    def has(self, key: str) -> bool:
        """
        Check if a key exists in memory.
        
        Args:
            key: The key to check.
            
        Returns:
            True if key exists, False otherwise.
            
        Raises:
            RuntimeError: If no backend is loaded.
        """
        if self._backend is None:
            raise RuntimeError("No memory backend loaded.")
        return self._backend.exists(key)
    
    def clear(self) -> None:
        """
        Clear all memory.
        
        Raises:
            RuntimeError: If no backend is loaded.
        """
        if self._backend is None:
            raise RuntimeError("No memory backend loaded.")
        self._backend.clear()
        self.logger.info("Memory cleared.")
    
    def list_keys(self) -> list[str]:
        """
        Return all stored keys.
        
        Returns:
            List of keys.
            
        Raises:
            RuntimeError: If no backend is loaded.
        """
        if self._backend is None:
            raise RuntimeError("No memory backend loaded.")
        return self._backend.keys()
    
    def count(self) -> int:
        """
        Return number of stored items.
        
        Returns:
            Count of items.
            
        Raises:
            RuntimeError: If no backend is loaded.
        """
        if self._backend is None:
            raise RuntimeError("No memory backend loaded.")
        return self._backend.count()
    
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
