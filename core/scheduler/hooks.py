"""
ArcV1 Scheduler Hooks

Lifecycle hooks for scheduler events.
Components can register hooks to observe task execution.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from core.queue import TaskEntry


class SchedulerHook(ABC):
    """
    Abstract base for scheduler lifecycle hooks.
    
    Implementations receive notifications for:
    - Task dispatch
    - Task completion
    - Task failure
    - Task timeout
    """
    
    @abstractmethod
    def on_task_dispatched(self, task_entry: TaskEntry) -> None:
        """Called when a task is dispatched to an agent."""
        pass
    
    @abstractmethod
    def on_task_completed(self, task_entry: TaskEntry, result: Any) -> None:
        """Called when a task completes successfully."""
        pass
    
    @abstractmethod
    def on_task_failed(self, task_entry: TaskEntry, error: str) -> None:
        """Called when a task fails permanently."""
        pass
    
    @abstractmethod
    def on_task_timeout(self, task_entry: TaskEntry) -> None:
        """Called when a task times out."""
        pass


class LoggingHook(SchedulerHook):
    """Logs scheduler events."""
    
    def __init__(self) -> None:
        from core.logger import get_logger
        self._logger = get_logger("Scheduler.Execution")
    
    def on_task_dispatched(self, task_entry: TaskEntry) -> None:
        self._logger.debug(f"Dispatched: {task_entry.task.name}")
    
    def on_task_completed(self, task_entry: TaskEntry, result: Any) -> None:
        exec_time = task_entry.execution_time_ms or 0
        self._logger.info(f"Completed: {task_entry.task.name} ({exec_time:.0f}ms)")
    
    def on_task_failed(self, task_entry: TaskEntry, error: str) -> None:
        self._logger.error(f"Failed: {task_entry.task.name}: {error}")
    
    def on_task_timeout(self, task_entry: TaskEntry) -> None:
        self._logger.warning(f"Timeout: {task_entry.task.name}")