"""
ArcV1 Permission Context

Describes who is requesting what operation.
Used for permission evaluation throughout the runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class PermissionContext:
    """
    Context for permission evaluation.
    
    Attributes:
        agent_name: Name of the requesting agent.
        agent_role: Role of the requesting agent.
        resource_type: Type of resource being accessed (e.g., 'tool', 'model', 'file').
        resource_action: Action being performed (e.g., 'execute', 'read', 'write').
        resource_path: Specific resource identifier or path.
        resource_params: Additional parameters for the operation.
        timestamp: Time of the request.
        session_id: Optional session identifier.
    """
    agent_name: str
    agent_role: str = "agent"
    resource_type: str = ""
    resource_action: str = ""
    resource_path: Optional[str] = None
    resource_params: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize context to dictionary."""
        return {
            "agent_name": self.agent_name,
            "agent_role": self.agent_role,
            "resource_type": self.resource_type,
            "resource_action": self.resource_action,
            "resource_path": self.resource_path,
            "resource_params": self.resource_params,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
        }