from agents.base.lifecycle import AgentLifecycle

life = AgentLifecycle()

print(life.state)

life.initialize()
print(life.state)

life.ready()
print(life.state)

life.start()
print(life.state)

life.pause()
print(life.state)

life.start()
print(life.state)

life.stop()
print(life.state)