"""
ArcV1 Permission System

Validates access to dangerous operations.
Supports role-based access and policy evaluation.
"""

from core.permissions.system import PermissionSystem
from core.permissions.context import PermissionContext
from core.permissions.result import PermissionResult

__all__ = ["PermissionSystem", "PermissionContext", "PermissionResult"]