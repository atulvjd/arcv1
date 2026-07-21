from core.registry import Registry

registry = Registry()

registry.register("logger", object())
registry.register("events", object())
registry.register("config", object())

print("Count :", registry.count())
print("Items :", registry.list())
print("Exists logger :", registry.exists("logger"))

registry.unregister("events")

print("\nAfter removing events")

print("Count :", registry.count())
print("Items :", registry.list())