"""
ArcV1 Message Bus

Central message routing and delivery system.
Agents communicate through the bus, never directly.
Supports priorities, retries, acknowledgements, and TTL.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Optional

from core.logger import get_logger
from core.messaging.envelope import MessageEnvelope
from core.messaging.middleware import (
    LoggingMiddleware,
    MessageMiddleware,
    PriorityMiddleware,
    ValidationMiddleware,
)


@dataclass
class Subscription:
    """Represents a handler subscription."""
    handler: Callable[[MessageEnvelope], None]
    filter_channel: Optional[str] = None
    filter_event: Optional[str] = None


class MessageBus:
    """
    Central message routing and delivery system.
    
    Features:
    - Agent decoupling (agents never call each other)
    - Priority-based routing
    - Automatic retries with backoff
    - Acknowledgement tracking
    - Message filtering and middleware pipeline
    - Dead letter queue for failed messages
    - Thread-safe operations
    
    Future: Distributed execution via external message brokers.
    """
    
    def __init__(self) -> None:
        self._subscriptions: dict[str, list[Subscription]] = defaultdict(list)
        self._middleware: list[MessageMiddleware] = []
        self._dead_letter_queue: list[MessageEnvelope] = []
        self._pending_acks: dict[str, MessageEnvelope] = {}
        self._lock = Lock()
        self._logger = get_logger("MessageBus")
        
        # Register default middleware
        self._register_default_middleware()
    
    def _register_default_middleware(self) -> None:
        """Register built-in middleware."""
        self._middleware.append(ValidationMiddleware())
        self._middleware.append(PriorityMiddleware())
        self._middleware.append(LoggingMiddleware())
    
    def register_middleware(self, middleware: MessageMiddleware) -> None:
        """
        Register middleware in the processing pipeline.
        
        Args:
            middleware: The middleware instance to add.
        """
        with self._lock:
            self._middleware.append(middleware)
    
    def subscribe(
        self,
        agent_name: str,
        handler: Callable[[MessageEnvelope], None],
        channel: Optional[str] = None,
        event_filter: Optional[str] = None
    ) -> None:
        """
        Subscribe an agent to receive messages.
        
        Args:
            agent_name: Name of the subscribing agent.
            handler: Callback to invoke on message receive.
            channel: Optional channel filter.
            event_filter: Optional event type filter.
        """
        subscription = Subscription(
            handler=handler,
            filter_channel=channel,
            filter_event=event_filter
        )
        with self._lock:
            self._subscriptions[agent_name].append(subscription)
        self._logger.debug(f"Agent '{agent_name}' subscribed.")
    
    def unsubscribe(
        self,
        agent_name: str,
        handler: Callable[[MessageEnvelope], None]
    ) -> None:
        """
        Remove a subscription.
        
        Args:
            agent_name: Name of the agent.
            handler: The handler to remove.
        """
        with self._lock:
            subs = self._subscriptions.get(agent_name, [])
            self._subscriptions[agent_name] = [
                s for s in subs if s.handler != handler
            ]
    
    def publish(self, envelope: MessageEnvelope) -> Optional[str]:
        """
        Publish a message to the bus.
        
        The message passes through middleware for processing
        before being routed to its destination.
        
        Args:
            envelope: The message envelope to publish.
            
        Returns:
            The envelope ID if published, None if filtered.
        """
        # Process through outbound middleware pipeline
        with self._lock:
            for middleware in self._middleware:
                envelope = middleware.process_outbound(envelope)
                if envelope is None:
                    self._logger.debug("Message filtered by middleware.")
                    return None
        
        # Route to destination
        self._route(envelope)
        
        return envelope.envelope_id
    
    def _route(self, envelope: MessageEnvelope) -> None:
        """Route envelope to appropriate subscribers."""
        destination = envelope.destination
        
        # Handle broadcast
        if destination == "*":
            self._broadcast(envelope)
            return
        
        # Direct delivery
        with self._lock:
            subscriptions = list(self._subscriptions.get(destination, []))
        
        for sub in subscriptions:
            # Check channel filter
            if sub.filter_channel and sub.filter_channel != envelope.channel:
                continue
            # Check event filter
            if sub.filter_event and sub.filter_event != envelope.message.event:
                continue
            self._deliver(envelope, sub.handler)
    
    def _broadcast(self, envelope: MessageEnvelope) -> None:
        """Broadcast to all subscribers."""
        with self._lock:
            all_subs = [
                (name, sub)
                for name, subs in self._subscriptions.items()
                for sub in subs
            ]
        
        for agent_name, sub in all_subs:
            if sub.filter_channel and sub.filter_channel != envelope.channel:
                continue
            self._deliver(envelope, sub.handler)
    
    def _deliver(
        self,
        envelope: MessageEnvelope,
        handler: Callable[[MessageEnvelope], None]
    ) -> None:
        """Deliver message to a handler through inbound middleware."""
        # Process through inbound middleware
        with self._lock:
            for middleware in self._middleware:
                envelope = middleware.process_inbound(envelope)
                if envelope is None:
                    return
        
        try:
            handler(envelope)
            envelope.mark_delivered()
            
            # Track for acknowledgement if required
            if envelope.require_ack:
                with self._lock:
                    self._pending_acks[envelope.envelope_id] = envelope
                    
        except Exception as e:
            self._handle_delivery_failure(envelope, e)
    
    def acknowledge(self, envelope_id: str) -> None:
        """
        Acknowledge receipt of a message.
        
        Args:
            envelope_id: The ID of the envelope to acknowledge.
        """
        with self._lock:
            self._pending_acks.pop(envelope_id, None)
    
    def _handle_delivery_failure(
        self,
        envelope: MessageEnvelope,
        error: Exception
    ) -> None:
        """Handle failed delivery with retry logic."""
        self._logger.error(
            f"Delivery failed for {envelope.envelope_id}: {error}"
        )
        
        if envelope.increment_retry():
            # Re-queue for retry
            self._route(envelope)
            self._logger.debug(
                f"Retry {envelope.retry_count}/{envelope.max_retries} "
                f"for {envelope.envelope_id}"
            )
        else:
            # Move to dead letter queue
            with self._lock:
                self._dead_letter_queue.append(envelope)
            self._logger.warning(
                f"Message moved to DLQ: {envelope.envelope_id}"
            )
    
    def get_pending_acks(self) -> list[str]:
        """Return IDs of messages awaiting acknowledgement."""
        with self._lock:
            return list(self._pending_acks.keys())
    
    def get_dead_letters(self) -> list[MessageEnvelope]:
        """Retrieve failed messages for inspection."""
        with self._lock:
            return self._dead_letter_queue.copy()
    
    def clear_dead_letters(self) -> None:
        """Clear the dead letter queue."""
        with self._lock:
            self._dead_letter_queue.clear()
    
    def clear(self) -> None:
        """Remove all subscriptions and pending messages."""
        with self._lock:
            self._subscriptions.clear()
            self._pending_acks.clear()
            self._dead_letter_queue.clear()
    
    def health_check(self) -> dict[str, Any]:
        """Return health check information."""
        with self._lock:
            return {
                "subscription_count": sum(
                    len(subs) for subs in self._subscriptions.values()
                ),
                "pending_acks": len(self._pending_acks),
                "dead_letter_count": len(self._dead_letter_queue),
                "middleware_count": len(self._middleware),
            }