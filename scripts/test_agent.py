from agents.base.agent import BaseAgent
from agents.base.context import AgentContext
from agents.base.message import Message
from agents.base.task import Task

from core.config import Config
from core.events import EventBus
from core.registry import Registry


class DummyAgent(BaseAgent):

    def on_initialize(self):
        print("Dummy initialized")

    def on_start(self):
        print("Dummy running")

    def on_stop(self):
        print("Dummy stopped")

    def on_execute(self, task: Task):
        print(f"Executing {task.name}")

    def on_message(self, message: Message):
        print(f"Message: {message.event}")


context = AgentContext(
    config=Config(),
    registry=Registry(),
    events=EventBus(),
)

agent = DummyAgent(
    name="Dummy",
    context=context,
)

agent.start()

task = Task(
    name="Test Task",
    description="Testing BaseAgent",
)

agent.execute(task)

message = Message(
    sender="Kernel",
    receiver="Dummy",
    event="hello",
)

agent.receive(message)

agent.stop()