from agents.base.context import AgentContext

from core.config import Config
from core.events import EventBus
from core.registry import Registry

context = AgentContext(
    config=Config(),
    registry=Registry(),
    events=EventBus(),
)

print(context)