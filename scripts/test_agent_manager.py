from agents.base.agent import BaseAgent
from agents.base.context import AgentContext
from agents.base.message import Message
from agents.base.task import Task
from agents.manager import AgentManager

from core.config import Config
from core.events import EventBus
from core.registry import Registry


class DummyAgent(BaseAgent):

    def on_initialize(self):
        print(f"{self.name} initialized")

    def on_start(self):
        print(f"{self.name} started")

    def on_stop(self):
        print(f"{self.name} stopped")

    def on_execute(self, task):
        print(f"{self.name} executing {task.name}")

    def on_message(self, message):
        print(f"{self.name} received {message.event}")


context = AgentContext(
    config=Config(),
    registry=Registry(),
    events=EventBus(),
)

manager = AgentManager()

newt = DummyAgent("Newt", context)
codex = DummyAgent("Codex", context)

manager.register(newt)
manager.register(codex)

print(manager.list())

manager.start_all()

manager.broadcast(
    Message(
        sender="Kernel",
        receiver="*",
        event="startup"
    )
)

manager.execute(
    "Newt",
    Task(
        name="Say Hello",
        description="Simple test"
    )
)

manager.stop_all()