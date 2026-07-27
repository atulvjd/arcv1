"""
ArcV1 Permission System

Validates access to dangerous operations.
Supports role-based access, policy evaluation, and rule chains.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from core.logger import get_logger
from core.permissions.context import PermissionContext
from core.permissions.result import PermissionResult


class PermissionRule(ABC):
    """
    Abstract base for permission rules.
    
    Each rule evaluates a PermissionContext and returns
    True (allowed), False (denied), or None (abstain).
    """
    
    def __init__(self, name: str) -> None:
        self.name = name
    
    @abstractmethod
    def evaluate(self, context: PermissionContext) -> Optional[bool]:
        """
        Evaluate the rule against the context.
        
        Args:
            context: Permission context to evaluate.
            
        Returns:
            True if allowed, False if denied, None if rule doesn't apply.
        """
        pass


class AllowAllRule(PermissionRule):
    """Allows everything (development mode)."""
    
    def __init__(self) -> None:
        super().__init__("allow_all")
    
    def evaluate(self, context: PermissionContext) -> bool:
        return True


class DenyAllRule(PermissionRule):
    """Denies everything (lockdown mode)."""
    
    def __init__(self) -> None:
        super().__init__("deny_all")
    
    def evaluate(self, context: PermissionContext) -> bool:
        return False


class RoleBasedRule(PermissionRule):
    """
    Role-based access control rule.
    
    Checks if the agent's role has permission for the given action.
    """
    
    ROLE_PERMISSIONS: dict[str, list[str]] = {
        "admin": ["*:*"],
        "developer": ["*:read", "*:write", "filesystem:*", "terminal:execute"],
        "operator": ["*:read", "filesystem:read"],
        "agent": ["*:read", "filesystem:read"],
        "guest": ["*:read"],
    }
    
    def __init__(self) -> None:
        super().__init__("role_based")
    
    def evaluate(self, context: PermissionContext) -> Optional[bool]:
        allowed = self.ROLE_PERMISSIONS.get(context.agent_role, [])
        resource = f"{context.resource_type}:{context.resource_action}"
        
        for pattern in allowed:
            if pattern == "*:*":
                return True
            if context.resource_type and pattern == f"*:{context.resource_action}":
                return True
            if context.resource_action and pattern == f"{context.resource_type}:*":
                return True
            if pattern == resource:
                return True
        
        return None  # Abstain - let other rules decide


class PermissionPolicy:
    """
    A named collection of rules evaluated in order.
    
    Evaluation follows: deny-first, then allow, then abstain.
    """
    
    def __init__(self, name: str, rules: list[PermissionRule]) -> None:
        self.name = name
        self.rules = rules
    
    def evaluate(self, context: PermissionContext) -> PermissionResult:
        """
        Evaluate the policy against the context.
        
        Rules are evaluated in order.
        First definitive answer (True/False) wins.
        If all rules abstain, policy denies by default.
        """
        evaluated: list[str] = []
        
        for rule in self.rules:
            evaluated.append(rule.name)
            result = rule.evaluate(context)
            
            if result is True:
                return PermissionResult(
                    allowed=True,
                    reason=f"Allowed by rule '{rule.name}' in policy '{self.name}'",
                    policy_name=self.name,
                    evaluated_rules=evaluated,
                    context=context
                )
            elif result is False:
                return PermissionResult(
                    allowed=False,
                    reason=f"Denied by rule '{rule.name}' in policy '{self.name}'",
                    policy_name=self.name,
                    evaluated_rules=evaluated,
                    context=context
                )
        
        # Default deny if no rule matched
        return PermissionResult(
            allowed=False,
            reason=f"No matching rule in policy '{self.name}'",
            policy_name=self.name,
            evaluated_rules=evaluated,
            context=context
        )


class PermissionSystem:
    """
    Central permission validation system.
    
    Manages policies and evaluates access requests.
    Provides a single point for permission enforcement.
    """
    
    def __init__(self) -> None:
        self._policies: dict[str, PermissionPolicy] = {}
        self._active_policy: Optional[str] = None
        self._logger = get_logger("PermissionSystem")
    
    def add_policy(self, policy: PermissionPolicy) -> None:
        """
        Add a permission policy.
        
        Args:
            policy: The policy to add.
        """
        self._policies[policy.name] = policy
        self._logger.debug(f"Policy added: {policy.name}")
    
    def set_active_policy(self, policy_name: str) -> None:
        """
        Set the active policy.
        
        Args:
            policy_name: Name of the policy to activate.
            
        Raises:
            KeyError: If policy not found.
        """
        if policy_name not in self._policies:
            raise KeyError(f"Policy '{policy_name}' not found.")
        self._active_policy = policy_name
        self._logger.info(f"Active policy set to: {policy_name}")
    
    def check_permission(self, context: PermissionContext) -> PermissionResult:
        """
        Check if an operation is permitted.
        
        Args:
            context: Permission context describing the request.
            
        Returns:
            PermissionResult with allow/deny decision.
        """
        policy_name = self._active_policy
        
        if policy_name is None:
            # Default: allow if no policy set (development mode)
            return PermissionResult(
                allowed=True,
                reason="No active policy - default allow",
                policy_name="default",
                evaluated_rules=["default_allow"]
            )
        
        policy = self._policies.get(policy_name)
        if policy is None:
            return PermissionResult(
                allowed=False,
                reason=f"Active policy '{policy_name}' not found",
                policy_name=policy_name,
                evaluated_rules=[]
            )
        
        return policy.evaluate(context)
    
    def setup_default_policies(self) -> None:
        """Set up default permission policies."""
        # Development policy: permissive
        dev_policy = PermissionPolicy(
            "development",
            [AllowAllRule()]
        )
        self.add_policy(dev_policy)
        
        # Restricted policy: role-based
        restricted_policy = PermissionPolicy(
            "restricted",
            [RoleBasedRule(), DenyAllRule()]
        )
        self.add_policy(restricted_policy)
        
        # Production policy: strict role-based
        admin_policy = PermissionPolicy(
            "production",
            [RoleBasedRule()]
        )
        self.add_policy(admin_policy)
        
        # Set development as default
        self.set_active_policy("development")
    
    def health_check(self) -> dict[str, Any]:
        """Return permission system health."""
        return {
            "active_policy": self._active_policy,
            "policy_count": len(self._policies),
            "policies": list(self._policies.keys()),
        }