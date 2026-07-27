"""
ArcV1 Messaging Layer

Provides decoupled communication between components.
Agents never call each other directly.
They communicate through the MessageBus.
"""

from core.messaging.bus import MessageBus
from core.messaging.envelope import MessageEnvelope
from core.messaging.middleware import MessageMiddleware
from core.messaging.router import MessageRouter

__all__ = [
    "MessageBus",
    "MessageEnvelope",
    "MessageMiddleware",
    "MessageRouter",
]