"""
ArcV1 Message Envelope

Wraps a Message with routing and delivery metadata.
Enables priority, retries, acknowledgements, and TTL.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from agents.base.message import Message


class MessagePriority:
    """Message priority levels (higher = more urgent)."""
    LOWEST = 0
    LOW = 25
    NORMAL = 50
    HIGH = 75
    CRITICAL = 100


@dataclass
class MessageEnvelope:
    """
    Wrapper around Message with routing and delivery metadata.
    
    Attributes:
        message: The core Message being sent.
        source: Sender identifier.
        destination: Target identifier or "*" for broadcast.
        channel: Logical channel for routing.
        priority: Message priority (higher = more urgent).
        envelope_id: Unique identifier for this envelope.
        correlation_id: For request/reply pattern matching.
        reply_to: Queue/channel for reply messages.
        created_at: Timestamp of creation.
        delivered_at: Timestamp of delivery (set after delivery).
        require_ack: Whether sender expects acknowledgement.
        max_retries: Maximum delivery attempts.
        retry_count: Current retry attempt number.
        ttl_seconds: Time-to-live in seconds (None = no expiry).
    """
    message: Message
    source: str
    destination: str
    channel: str = "default"
    priority: int = MessagePriority.NORMAL
    
    envelope_id: str = field(default_factory=lambda: str(uuid4()))
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    
    created_at: datetime = field(default_factory=datetime.now)
    delivered_at: Optional[datetime] = None
    
    require_ack: bool = False
    max_retries: int = 3
    retry_count: int = 0
    ttl_seconds: Optional[int] = None
    
    @property
    def is_expired(self) -> bool:
        """Check if the envelope has exceeded its TTL."""
        if self.ttl_seconds is None:
            return False
        elapsed = (datetime.now() - self.created_at).total_seconds()
        return elapsed > self.ttl_seconds
    
    def increment_retry(self) -> bool:
        """
        Increment retry count.
        
        Returns:
            True if should retry, False if max retries exceeded.
        """
        self.retry_count += 1
        return self.retry_count < self.max_retries
    
    def mark_delivered(self) -> None:
        """Mark as delivered with current timestamp."""
        self.delivered_at = datetime.now()
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "envelope_id": self.envelope_id,
            "source": self.source,
            "destination": self.destination,
            "channel": self.channel,
            "priority": self.priority,
            "correlation_id": self.correlation_id,
            "created_at": self.created_at.isoformat(),
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "require_ack": self.require_ack,
            "retry_count": self.retry_count,
            "message": {
                "sender": self.message.sender,
                "receiver": self.message.receiver,
                "event": self.message.event,
                "payload": self.message.payload,
                "id": self.message.id,
                "timestamp": self.message.timestamp.isoformat()
            }
        }