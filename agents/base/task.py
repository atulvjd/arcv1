"""
ArcV1 Task System
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any
from uuid import uuid4


class TaskStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass(slots=True)
class Task:
    """
    Represents a unit of work executed by an agent.
    """

    name: str
    description: str

    data: dict[str, Any] = field(default_factory=dict)

    id: str = field(default_factory=lambda: str(uuid4()))

    created_at: datetime = field(default_factory=datetime.now)

    status: TaskStatus = TaskStatus.PENDING