"""
ArcV1 Permission Result

Represents the outcome of a permission check.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class PermissionResult:
    """
    Result of a permission evaluation.
    
    Attributes:
        allowed: Whether the operation is permitted.
        reason: Human-readable explanation.
        policy_name: Name of the policy that matched.
        evaluated_rules: List of rules evaluated.
        context: The original permission context.
        evaluated_at: Timestamp of evaluation.
    """
    allowed: bool
    reason: str = ""
    policy_name: Optional[str] = None
    evaluated_rules: list[str] = field(default_factory=list)
    context: Any = None
    evaluated_at: datetime = field(default_factory=datetime.now)
    
    @classmethod
    def allow(cls, reason: str = "Allowed", policy: Optional[str] = None) -> "PermissionResult":
        """Create an allowed result."""
        return cls(allowed=True, reason=reason, policy_name=policy)
    
    @classmethod
    def deny(cls, reason: str = "Denied", policy: Optional[str] = None) -> "PermissionResult":
        """Create a denied result."""
        return cls(allowed=False, reason=reason, policy_name=policy)
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "policy": self.policy_name,
            "rules": self.evaluated_rules,
            "evaluated_at": self.evaluated_at.isoformat(),
        }