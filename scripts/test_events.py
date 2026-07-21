from core.events import EventBus

events = EventBus()


def logger(message: str) -> None:
    print(f"[LOGGER] {message}")


def newt(message: str) -> None:
    print(f"[NEWT] {message}")


def codex(message: str) -> None:
    print(f"[CODEX] {message}")


events.subscribe("runtime.started", logger)
events.subscribe("runtime.started", newt)
events.subscribe("runtime.started", codex)

events.emit("runtime.started", "ArcV1 Runtime Started")
events.unsubscribe("runtime.started", codex)

print("\nAfter removing CODEX:\n")

events.emit("runtime.started", "Runtime Restarted")