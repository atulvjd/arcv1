"""
ArcV1 Base Service

Defines the common lifecycle and interface for all ArcV1 services.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional

from core.logger import get_logger


class ServiceState(Enum):
    """Service lifecycle states."""
    CREATED = "created"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class BaseService(ABC):
    """
    Abstract base class for all ArcV1 services.
    
    Provides common lifecycle management and interface requirements.
    Services should implement on_initialize, on_start, and on_stop.
    """
    
    def __init__(self, name: str) -> None:
        """
        Initialize the service.
        
        Args:
            name: Unique name identifying this service.
        """
        self.name = name
        self.logger = get_logger(name)
        self._state = ServiceState.CREATED
        self._config: dict[str, Any] = {}
    
    @property
    def state(self) -> ServiceState:
        """Return current service state."""
        return self._state
    
    @property
    def is_running(self) -> bool:
        """Check if service is currently running."""
        return self._state == ServiceState.RUNNING
    
    def configure(self, config: dict[str, Any]) -> None:
        """
        Configure the service with a configuration dictionary.
        
        Args:
            config: Configuration parameters.
        """
        self._config = config
        self.logger.debug(f"Service configured with {len(config)} parameters.")
    
    def initialize(self) -> None:
        """
        Initialize the service.
        
        Transitions: CREATED -> INITIALIZING -> INITIALIZED
        """
        if self._state != ServiceState.CREATED:
            self.logger.warning(f"Cannot initialize service in state {self._state.value}")
            return
        
        self.logger.info("Initializing service...")
        self._state = ServiceState.INITIALIZING
        
        try:
            self.on_initialize()
            self._state = ServiceState.INITIALIZED
            self.logger.info("Service initialized successfully.")
        except Exception as e:
            self._state = ServiceState.ERROR
            self.logger.error(f"Failed to initialize service: {e}")
            raise
    
    def start(self) -> None:
        """
        Start the service.
        
        Transitions: INITIALIZED -> STARTING -> RUNNING
        """
        if self._state != ServiceState.INITIALIZED:
            self.logger.warning(f"Cannot start service in state {self._state.value}")
            return
        
        self.logger.info("Starting service...")
        self._state = ServiceState.STARTING
        
        try:
            self.on_start()
            self._state = ServiceState.RUNNING
            self.logger.info("Service started successfully.")
        except Exception as e:
            self._state = ServiceState.ERROR
            self.logger.error(f"Failed to start service: {e}")
            raise
    
    def stop(self) -> None:
        """
        Stop the service.
        
        Transitions: RUNNING -> STOPPING -> STOPPED
        """
        if self._state != ServiceState.RUNNING:
            self.logger.warning(f"Cannot stop service in state {self._state.value}")
            return
        
        self.logger.info("Stopping service...")
        self._state = ServiceState.STOPPING
        
        try:
            self.on_stop()
            self._state = ServiceState.STOPPED
            self.logger.info("Service stopped successfully.")
        except Exception as e:
            self._state = ServiceState.ERROR
            self.logger.error(f"Failed to stop service: {e}")
            raise
    
    @abstractmethod
    def on_initialize(self) -> None:
        """
        Custom initialization logic.
        
        Implementations should set up any internal state needed for the service.
        """
        pass
    
    @abstractmethod
    def on_start(self) -> None:
        """
        Custom start logic.
        
        Implementations should perform any actions needed when the service starts.
        """
        pass
    
    @abstractmethod
    def on_stop(self) -> None:
        """
        Custom stop logic.
        
        Implementations should clean up any resources when the service stops.
        """
        pass
    
    def shutdown(self) -> None:
        """
        Shutdown the service (alias for stop).
        
        Provided for backward compatibility.
        """
        self.stop()
    
    def health_check(self) -> dict[str, Any]:
        """
        Perform a health check.
        
        Returns:
            Dictionary with health status information.
        """
        return {
            "service": self.name,
            "state": self.state.value,
            "is_running": self.is_running
        }
