from agents.base.message import Message

message = Message(
    sender="Kernel",
    receiver="Newt",
    event="startup",
    payload={
        "status": "ready",
        "version": "0.1"
    }
)

print(message)