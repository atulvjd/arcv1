from core.runtime import Runtime

runtime = Runtime()

print(f"Status: {runtime.status()}")

runtime.start()

print(f"Status: {runtime.status()}")

runtime.restart()

print(f"Status: {runtime.status()}")

runtime.stop()

print(f"Status: {runtime.status()}")