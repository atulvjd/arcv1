"""
ArcV1 Message Router

Intelligent message routing with pattern matching.
Supports direct, broadcast, topic-based, and request/reply patterns.
"""

from __future__ import annotations

import threading
from collections import defaultdict
from typing import Any, Callable, Optional
from uuid import uuid4

from agents.base.message import Message
from core.logger import get_logger
from core.messaging.bus import MessageBus
from core.messaging.envelope import MessageEnvelope, MessagePriority


class MessageRouter:
    """
    Intelligent message routing with pattern matching.

    Features:
    - Direct routing (agent-to-agent)
    - Broadcast routing (one-to-all)
    - Topic-based routing (pub/sub patterns)
    - Request/reply pattern support

    This is a higher-level abstraction over MessageBus.
    Agents and components use this for structured communication.
    """

    def __init__(self, bus: MessageBus) -> None:
        """
        Initialize the router.

        Args:
            bus: The MessageBus instance to route through.
        """
        self._bus = bus
        self._topic_subscriptions: dict[str, list[str]] = defaultdict(list)
        self._request_handlers: dict[str, Callable] = {}
        self._logger = get_logger("MessageRouter")

    def subscribe_topic(self, agent_name: str, topic: str) -> None:
        """
        Subscribe an agent to a topic.

        Args:
            agent_name: Name of the subscribing agent.
            topic: Topic string to subscribe to.
        """
        self._topic_subscriptions[topic].append(agent_name)
        self._logger.debug(f"Agent '{agent_name}' subscribed to topic '{topic}'")

    def unsubscribe_topic(self, agent_name: str, topic: str) -> None:
        """
        Unsubscribe an agent from a topic.

        Args:
            agent_name: Name of the agent.
            topic: Topic to unsubscribe from.
        """
        if topic in self._topic_subscriptions:
            self._topic_subscriptions[topic] = [
                a for a in self._topic_subscriptions[topic]
                if a != agent_name
            ]

    def publish_topic(
        self,
        topic: str,
        message: Message,
        source: str,
        priority: int = MessagePriority.NORMAL
    ) -> list[str]:
        """
        Publish a message to all topic subscribers.

        Args:
            topic: Topic to publish to.
            message: The Message to publish.
            source: Source identifier.
            priority: Message priority.

        Returns:
            List of envelope IDs for tracking.
        """
        envelope_ids: list[str] = []
        subscribers = self._topic_subscriptions.get(topic, [])

        for subscriber in subscribers:
            envelope = MessageEnvelope(
                message=Message(
                    sender=source,
                    receiver=subscriber,
                    event=message.event or "topic",
                    payload=message.payload
                ),
                source=source,
                destination=subscriber,
                channel=f"topic:{topic}",
                priority=priority
            )
            env_id = self._bus.publish(envelope)
            if env_id:
                envelope_ids.append(env_id)

        return envelope_ids

    def send_direct(
        self,
        source: str,
        destination: str,
        event: str,
        payload: dict[str, Any],
        priority: int = MessagePriority.NORMAL,
        require_ack: bool = False
    ) -> Optional[str]:
        """
        Send a direct message to a specific agent.

        Args:
            source: Sender name.
            destination: Target agent name.
            event: Event type.
            payload: Message payload.
            priority: Message priority.
            require_ack: Whether acknowledgement is required.

        Returns:
            Envelope ID if published, None otherwise.
        """
        message = Message(
            sender=source,
            receiver=destination,
            event=event,
            payload=payload
        )

        envelope = MessageEnvelope(
            message=message,
            source=source,
            destination=destination,
            priority=priority,
            require_ack=require_ack
        )

        return self._bus.publish(envelope)

    def broadcast(
        self,
        source: str,
        event: str,
        payload: dict[str, Any],
        priority: int = MessagePriority.NORMAL
    ) -> Optional[str]:
        """
        Broadcast a message to all agents.

        Args:
            source: Sender name.
            event: Event type.
            payload: Message payload.
            priority: Message priority.

        Returns:
            Envelope ID if published.
        """
        message = Message(
            sender=source,
            receiver="*",
            event=event,
            payload=payload
        )

        envelope = MessageEnvelope(
            message=message,
            source=source,
            destination="*",
            priority=priority
        )

        return self._bus.publish(envelope)

    def request(
        self,
        source: str,
        target: str,
        event: str,
        payload: dict[str, Any],
        timeout: float = 30.0
    ) -> Optional[MessageEnvelope]:
        """
        Send a request and expect a reply.

        Implements the request/reply pattern.
        Currently synchronous. Future: async with futures.

        Args:
            source: Sender name.
            target: Target agent name.
            event: Request event type.
            payload: Request payload.
            timeout: Maximum wait time in seconds.

        Returns:
            Reply envelope, or None on timeout.
        """
        correlation_id = str(uuid4())

        message = Message(
            sender=source,
            receiver=target,
            event=f"request:{event}",
            payload=payload
        )

        envelope = MessageEnvelope(
            message=message,
            source=source,
            destination=target,
            correlation_id=correlation_id,
            reply_to=f"__reply:{source}",
            require_ack=True,
            ttl_seconds=int(timeout)
        )

        reply_event = threading.Event()
        reply: Optional[MessageEnvelope] = None

        def handle_reply(env: MessageEnvelope) -> None:
            nonlocal reply
            if env.correlation_id == correlation_id:
                reply = env
                reply_event.set()

        self._bus.subscribe(source, handle_reply, channel=f"__reply:{source}")
        self._bus.publish(envelope)

        reply_event.wait(timeout=timeout)
        self._bus.unsubscribe(source, handle_reply)

        return reply

    def reply(
        self,
        original: MessageEnvelope,
        source: str,
        payload: dict[str, Any]
    ) -> Optional[str]:
        """
        Reply to a request.

        Args:
            original: The original request envelope.
            source: Reply sender name.
            payload: Reply payload.

        Returns:
            Envelope ID if published.
        """
        if not original.reply_to:
            return None

        message = Message(
            sender=source,
            receiver=original.source,
            event=f"reply:{original.message.event}",
            payload=payload
        )

        envelope = MessageEnvelope(
            message=message,
            source=source,
            destination=original.source,
            channel=original.reply_to,
            correlation_id=original.correlation_id
        )

        return self._bus.publish(envelope)

    def health_check(self) -> dict[str, Any]:
        """Return health check information."""
        return {
            "topic_count": len(self._topic_subscriptions),
            "total_subscribers": sum(
                len(subs) for subs in self._topic_subscriptions.values()
            ),
        }
