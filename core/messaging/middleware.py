"""
ArcV1 Message Middleware

Processing pipeline for messages passing through the bus.
Middleware can inspect, modify, filter, or log messages.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from core.logger import get_logger
from core.messaging.envelope import MessageEnvelope


class MessageMiddleware(ABC):
    """
    Abstract base class for message processing middleware.
    
    Middleware is called in order during message routing.
    Returning None from either method filters the message.
    """
    
    @abstractmethod
    def process_outbound(self, envelope: MessageEnvelope) -> Optional[MessageEnvelope]:
        """
        Process message before routing.
        
        Args:
            envelope: The outgoing message envelope.
            
        Returns:
            Modified envelope, or None to filter/drop.
        """
        pass
    
    @abstractmethod
    def process_inbound(self, envelope: MessageEnvelope) -> Optional[MessageEnvelope]:
        """
        Process message before delivery.
        
        Args:
            envelope: The incoming message envelope.
            
        Returns:
            Modified envelope, or None to filter/drop.
        """
        pass


class LoggingMiddleware(MessageMiddleware):
    """Logs all messages passing through the bus."""
    
    def __init__(self) -> None:
        self._logger = get_logger("MessageBus.Logging")
    
    def process_outbound(self, envelope: MessageEnvelope) -> MessageEnvelope:
        self._logger.debug(
            f"OUTBOUND: {envelope.source} -> {envelope.destination} "
            f"[{envelope.message.event}] pri={envelope.priority}"
        )
        return envelope
    
    def process_inbound(self, envelope: MessageEnvelope) -> MessageEnvelope:
        self._logger.debug(
            f"INBOUND: {envelope.source} -> {envelope.destination} "
            f"[{envelope.message.event}]"
        )
        return envelope


class RetryMiddleware(MessageMiddleware):
    """Assigns default retry configuration to outbound messages."""
    
    def __init__(self, max_retries: int = 3) -> None:
        self._max_retries = max_retries
    
    def process_outbound(self, envelope: MessageEnvelope) -> MessageEnvelope:
        if envelope.max_retries == 3:  # Only set if not explicitly configured
            envelope.max_retries = self._max_retries
        return envelope
    
    def process_inbound(self, envelope: MessageEnvelope) -> MessageEnvelope:
        return envelope


class ValidationMiddleware(MessageMiddleware):
    """Validates message structure and content."""
    
    def process_outbound(self, envelope: MessageEnvelope) -> Optional[MessageEnvelope]:
        if not envelope.source:
            self._logger = get_logger("MessageBus.Validation")
            self._logger.warning("Message missing source, dropping.")
            return None
        if not envelope.message.event:
            self._logger = get_logger("MessageBus.Validation")
            self._logger.warning("Message missing event type, dropping.")
            return None
        return envelope
    
    def process_inbound(self, envelope: MessageEnvelope) -> Optional[MessageEnvelope]:
        if envelope.is_expired:
            self._logger = get_logger("MessageBus.Validation")
            self._logger.debug(f"Expired message dropped: {envelope.envelope_id}")
            return None
        return envelope


class PriorityMiddleware(MessageMiddleware):
    """Ensures priority is within valid range."""
    
    def process_outbound(self, envelope: MessageEnvelope) -> MessageEnvelope:
        envelope.priority = max(0, min(100, envelope.priority))
        return envelope
    
    def process_inbound(self, envelope: MessageEnvelope) -> MessageEnvelope:
        return envelope