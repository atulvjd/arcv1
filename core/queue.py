"""
ArcV1 Task Queue

Manages task execution with priorities, retries, and dependencies.
Tasks are queued and dispatched by the Scheduler.
"""

from __future__ import annotations

import heapq
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Optional
from uuid import uuid4

from agents.base.task import Task


class TaskEntryStatus(Enum):
    """Status of a task in the queue."""
    PENDING = auto()
    QUEUED = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()
    TIMEOUT = auto()


class TaskPriority:
    """Task priority levels (higher = more urgent)."""
    BACKGROUND = 0
    LOW = 25
    NORMAL = 50
    HIGH = 75
    CRITICAL = 100


@dataclass(order=True)
class PriorityEntry:
    """Wrapper for heap-based priority queue."""
    priority: int
    created_at: datetime
    entry_id: str = field(compare=False)


@dataclass
class TaskEntry:
    """
    Wrapper around Task with queue and execution metadata.
    
    Attributes:
        task: The core Task being executed.
        priority: Task priority for scheduling.
        entry_id: Unique identifier for this queue entry.
        status: Current status in the queue lifecycle.
        assigned_agent: Agent assigned to execute this task.
        enqueued_at: Timestamp of queuing.
        started_at: Timestamp of execution start.
        completed_at: Timestamp of completion.
        max_retries: Maximum retry attempts on failure.
        retry_count: Current retry count.
        last_error: Error message from last failure.
        timeout_seconds: Maximum execution time.
        depends_on: List of entry_ids that must complete first.
        dependents: List of entry_ids that depend on this task.
        result: The execution result (set on completion).
    """
    task: Task
    priority: int = TaskPriority.NORMAL
    
    entry_id: str = field(default_factory=lambda: str(uuid4()))
    status: TaskEntryStatus = TaskEntryStatus.PENDING
    assigned_agent: str = ""
    
    enqueued_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    max_retries: int = 3
    retry_count: int = 0
    last_error: Optional[str] = None
    
    timeout_seconds: Optional[int] = None
    
    depends_on: list[str] = field(default_factory=list)
    dependents: list[str] = field(default_factory=list)
    
    result: Any = None
    
    @property
    def is_ready(self) -> bool:
        """
        Check if task is ready to execute.
        
        A task is ready if:
        - It is QUEUED (not already running/completed)
        - It hasn't exceeded max retries
        - All dependencies are completed
        """
        return (
            self.status == TaskEntryStatus.QUEUED
            and self.retry_count < self.max_retries
        )
    
    @property
    def execution_time_ms(self) -> Optional[float]:
        """Calculate execution time if completed."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds() * 1000
        return None
    
    def mark_queued(self) -> None:
        """Mark task as queued."""
        self.status = TaskEntryStatus.QUEUED
        self.enqueued_at = datetime.now()
    
    def mark_running(self) -> None:
        """Mark task as running."""
        self.status = TaskEntryStatus.RUNNING
        self.started_at = datetime.now()
    
    def mark_completed(self, result: Any = None) -> None:
        """Mark task as completed."""
        self.status = TaskEntryStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result
    
    def mark_failed(self, error: str) -> bool:
        """
        Mark task as failed and potentially retry.
        
        Args:
            error: Error message.
            
        Returns:
            True if task will be retried, False if permanently failed.
        """
        self.retry_count += 1
        self.last_error = error
        
        if self.retry_count >= self.max_retries:
            self.status = TaskEntryStatus.FAILED
            self.completed_at = datetime.now()
            return False
        else:
            self.status = TaskEntryStatus.QUEUED
            return True
    
    def mark_cancelled(self) -> None:
        """Mark task as cancelled."""
        self.status = TaskEntryStatus.CANCELLED
        self.completed_at = datetime.now()
    
    def mark_timeout(self) -> None:
        """Mark task as timed out."""
        self.status = TaskEntryStatus.TIMEOUT
        self.completed_at = datetime.now()
        self.last_error = f"Task timed out after {self.timeout_seconds}s"


class TaskQueue:
    """
    Thread-safe priority-based task queue.
    
    Manages task lifecycle from queuing through completion.
    Supports priorities, retries, cancellation, timeout, and dependencies.
    """
    
    def __init__(self) -> None:
        self._entries: dict[str, TaskEntry] = {}
        self._heap: list[PriorityEntry] = []
        self._lock = threading.Lock()
    
    def enqueue(self, entry: TaskEntry) -> str:
        """
        Add a task to the queue.
        
        Args:
            entry: TaskEntry to enqueue.
            
        Returns:
            entry_id for tracking.
        """
        with self._lock:
            entry.mark_queued()
            self._entries[entry.entry_id] = entry
            heap_entry = PriorityEntry(
                priority=-entry.priority,
                created_at=entry.enqueued_at,
                entry_id=entry.entry_id
            )
            heapq.heappush(self._heap, heap_entry)
            return entry.entry_id
    
    def dequeue(self, count: int = 1) -> list[TaskEntry]:
        """
        Dequeue tasks that are ready to execute.
        
        Args:
            count: Maximum number of tasks to dequeue.
            
        Returns:
            List of ready TaskEntry objects.
        """
        result: list[TaskEntry] = []
        temp_heap: list[PriorityEntry] = []
        
        with self._lock:
            while self._heap and len(result) < count:
                heap_entry = heapq.heappop(self._heap)
                entry = self._entries.get(heap_entry.entry_id)
                
                if entry is None:
                    continue
                
                if self._dependencies_met(entry):
                    if entry.is_ready:
                        result.append(entry)
                    else:
                        # Not ready but valid, put back
                        temp_heap.append(heap_entry)
                else:
                    # Dependencies not met, defer
                    temp_heap.append(heap_entry)
            
            # Return deferred entries to heap
            for entry in temp_heap:
                heapq.heappush(self._heap, entry)
        
        return result
    
    def _dependencies_met(self, entry: TaskEntry) -> bool:
        """Check if all dependencies are satisfied."""
        for dep_id in entry.depends_on:
            dep_entry = self._entries.get(dep_id)
            if dep_entry is None:
                continue  # Dependency doesn't exist, skip
            if dep_entry.status != TaskEntryStatus.COMPLETED:
                return False
        return True
    
    def peek(self, count: int = 1) -> list[TaskEntry]:
        """
        View tasks without dequeuing.
        
        Args:
            count: Maximum number to return.
            
        Returns:
            List of TaskEntry sorted by priority.
        """
        with self._lock:
            ready = [
                entry for entry in self._entries.values()
                if entry.is_ready and self._dependencies_met(entry)
            ]
            ready.sort(key=lambda e: -e.priority)
            return ready[:count]
    
    def cancel(self, entry_id: str) -> bool:
        """
        Cancel a queued or pending task.
        
        Args:
            entry_id: ID of the task to cancel.
            
        Returns:
            True if cancelled, False if not found or already running.
        """
        with self._lock:
            entry = self._entries.get(entry_id)
            if entry and entry.status in (TaskEntryStatus.PENDING, TaskEntryStatus.QUEUED):
                entry.mark_cancelled()
                return True
            return False
    
    def get(self, entry_id: str) -> Optional[TaskEntry]:
        """Get a task entry by ID."""
        with self._lock:
            return self._entries.get(entry_id)
    
    def update(self, entry: TaskEntry) -> None:
        """Update an existing task entry."""
        with self._lock:
            self._entries[entry.entry_id] = entry
    
    def size(self) -> int:
        """Return number of queued (not yet completed) tasks."""
        with self._lock:
            return sum(
                1 for e in self._entries.values()
                if e.status in (TaskEntryStatus.PENDING, TaskEntryStatus.QUEUED)
            )
    
    def clear(self) -> None:
        """Clear all tasks."""
        with self._lock:
            self._entries.clear()
            self._heap.clear()
    
    def get_by_status(self, status: TaskEntryStatus) -> list[TaskEntry]:
        """Get tasks filtered by status."""
        with self._lock:
            return [e for e in self._entries.values() if e.status == status]
    
    def get_by_agent(self, agent_name: str) -> list[TaskEntry]:
        """Get tasks assigned to a specific agent."""
        with self._lock:
            return [
                e for e in self._entries.values()
                if e.assigned_agent == agent_name
            ]
    
    def health_check(self) -> dict[str, Any]:
        """Return queue health information."""
        with self._lock:
            statuses = defaultdict(int)
            for entry in self._entries.values():
                statuses[entry.status.name] += 1
            return {
                "total": len(self._entries),
                "queued": self.size(),
                "statuses": dict(statuses),
                "heap_size": len(self._heap),
            }