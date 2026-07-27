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
