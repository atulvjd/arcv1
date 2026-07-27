"""
ArcV1 Scheduler

Heartbeat of the ArcV1 runtime.
Consumes queued tasks, dispatches to workers, monitors execution.
"""

from __future__ import annotations

import threading
import time
from datetime import datetime
from typing import Any, Callable, Optional

from agents.base.agent import BaseAgent
from agents.manager import AgentManager
from core.events import EventBus
from core.logger import get_logger
from core.queue import TaskEntry, TaskEntryStatus, TaskQueue
from core.state import StateManager


class Scheduler:
    """
    Central task scheduler for ArcV1.
    
    Responsibilities:
    - Continuously consume queued tasks
    - Dispatch tasks to assigned agents
    - Monitor execution with timeouts
    - Handle retries on failure
    - Emit lifecycle events
    
    Architecture:
    Scheduler polls the queue in a loop.
    For each ready task, it creates an execution context
    and dispatches to the target agent.
    
    Future: Concurrent execution via thread/process pool.
    """
    
    def __init__(
        self,
        queue: TaskQueue,
        agent_manager: AgentManager,
        event_bus: EventBus,
        state_manager: StateManager | None = None,
    ) -> None:
        """
        Initialize the scheduler.
        
        Args:
            queue: TaskQueue instance.
            agent_manager: AgentManager for agent lookup.
            event_bus: EventBus for emitting lifecycle events.
            state_manager: Optional StateManager for health tracking.
        """
        self._queue = queue
        self._agent_manager = agent_manager
        self._event_bus = event_bus
        self._state_manager = state_manager
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._poll_interval: float = 0.1  # 100ms
        self._active_tasks: dict[str, threading.Thread] = {}
        self._hooks: list[SchedulerHook] = []
        self._lock = threading.Lock()
        self._logger = get_logger("Scheduler")
    
    @property
    def running(self) -> bool:
        """Check if the scheduler is running."""
        return self._running
    
    @property
    def active_task_count(self) -> int:
        """Return number of currently executing tasks."""
        with self._lock:
            return len(self._active_tasks)
    
    def add_hook(self, hook: "SchedulerHook") -> None:
        """Register a scheduler lifecycle hook."""
        self._hooks.append(hook)
    
    def start(self) -> None:
        """Start the scheduler loop."""
        if self._running:
            self._logger.warning("Scheduler is already running.")
            return
        
        self._running = True
        self._thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
            name="scheduler-loop"
        )
        self._thread.start()
        self._logger.info("Scheduler started.")
        self._event_bus.emit("scheduler.started")
    
    def stop(self) -> None:
        """Stop the scheduler loop gracefully."""
        if not self._running:
            return
        
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None
        
        self._logger.info("Scheduler stopped.")
        self._event_bus.emit("scheduler.stopped")
    
    def _run_loop(self) -> None:
        """Main scheduler polling loop."""
        while self._running:
            try:
                self._process_tick()
            except Exception as e:
                self._logger.error(f"Scheduler tick error: {e}")
            time.sleep(self._poll_interval)
    
    def _process_tick(self) -> None:
        """Process a single scheduler tick."""
        # Check for completed tasks
        self._check_completed()
        
        # Check for timeouts
        self._check_timeouts()
        
        # Dispatch new tasks if capacity available
        self._dispatch_tasks()
    
    def _dispatch_tasks(self) -> None:
        """Dispatch ready tasks to their agents."""
        # Limit concurrent execution
        max_concurrent = 4
        with self._lock:
            available = max_concurrent - len(self._active_tasks)
        
        if available <= 0:
            return
        
        tasks = self._queue.dequeue(count=available)
        
        for task_entry in tasks:
            self._execute_task(task_entry)
    
    def _execute_task(self, task_entry: TaskEntry) -> None:
        """Execute a task in a separate thread."""
        agent = self._agent_manager.get(task_entry.assigned_agent)
        
        if agent is None:
            self._logger.warning(
                f"Agent '{task_entry.assigned_agent}' not found for task "
                f"{task_entry.entry_id}"
            )
            task_entry.mark_failed(f"Agent '{task_entry.assigned_agent}' not found")
            self._queue.update(task_entry)
            return
        
        task_entry.mark_running()
        self._queue.update(task_entry)
        
        # Execute in thread
        thread = threading.Thread(
            target=self._run_task,
            args=(task_entry, agent),
            daemon=True,
            name=f"task-{task_entry.entry_id[:8]}"
        )
        
        with self._lock:
            self._active_tasks[task_entry.entry_id] = thread
        
        thread.start()
        
        # Notify hooks
        for hook in self._hooks:
            try:
                hook.on_task_dispatched(task_entry)
            except Exception:
                pass
        
        self._event_bus.emit(
            "task.dispatched",
            task_id=task_entry.entry_id,
            agent=agent.name,
            task_name=task_entry.task.name
        )
    
    def _run_task(self, task_entry: TaskEntry, agent: BaseAgent) -> None:
        """Run a task in its thread."""
        self._logger.debug(
            f"Executing task '{task_entry.task.name}' "
            f"on agent '{agent.name}'"
        )
        
        try:
            result = agent.execute(task_entry.task)
            task_entry.mark_completed(result)
            
            self._event_bus.emit(
                "task.completed",
                task_id=task_entry.entry_id,
                agent=agent.name,
                task_name=task_entry.task.name
            )
            
            # Notify hooks
            for hook in self._hooks:
                try:
                    hook.on_task_completed(task_entry, result)
                except Exception:
                    pass
                    
        except Exception as e:
            error_msg = str(e)
            self._logger.error(f"Task '{task_entry.task.name}' failed: {error_msg}")
            
            will_retry = task_entry.mark_failed(error_msg)
            
            if will_retry:
                self._event_bus.emit(
                    "task.retry",
                    task_id=task_entry.entry_id,
                    agent=agent.name,
                    retry_count=task_entry.retry_count,
                    error=error_msg
                )
                # Re-queue for retry
                self._queue.enqueue(task_entry)
            else:
                self._event_bus.emit(
                    "task.failed",
                    task_id=task_entry.entry_id,
                    agent=agent.name,
                    error=error_msg
                )
                
                for hook in self._hooks:
                    try:
                        hook.on_task_failed(task_entry, str(e))
                    except Exception:
                        pass
        finally:
            with self._lock:
                self._active_tasks.pop(task_entry.entry_id, None)
            self._queue.update(task_entry)
    
    def _check_completed(self) -> None:
        """Clean up completed task threads."""
        with self._lock:
            completed_ids = [
                tid for tid, thread in self._active_tasks.items()
                if not thread.is_alive()
            ]
            for tid in completed_ids:
                self._active_tasks.pop(tid, None)
    
    def _check_timeouts(self) -> None:
        """Check for running tasks that have exceeded timeout."""
        running_tasks = self._queue.get_by_status(TaskEntryStatus.RUNNING)
        now = datetime.now()
        
        for task_entry in running_tasks:
            if task_entry.timeout_seconds and task_entry.started_at:
                elapsed = (now - task_entry.started_at).total_seconds()
                if elapsed > task_entry.timeout_seconds:
                    task_entry.mark_timeout()
                    self._queue.update(task_entry)
                    
                    with self._lock:
                        thread = self._active_tasks.pop(task_entry.entry_id, None)
                    
                    self._logger.warning(
                        f"Task '{task_entry.task.name}' timed out "
                        f"after {task_entry.timeout_seconds}s"
                    )
                    
                    self._event_bus.emit(
                        "task.timeout",
                        task_id=task_entry.entry_id,
                        task_name=task_entry.task.name
                    )
    
    def health_check(self) -> dict[str, Any]:
        """Return scheduler health information."""
        return {
            "running": self._running,
            "active_tasks": self.active_task_count,
            "queue_size": self._queue.size(),
        }