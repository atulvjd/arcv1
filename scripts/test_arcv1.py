from core.runtime import Runtime

runtime = Runtime()

print("=" * 40)
print("        ArcV1 Integration Test")
print("=" * 40)

runtime.start()

print("\nRuntime Status:", runtime.status())

print("\nRegistered Components:")

for component in runtime.kernel.registry.list():
    print(f" - {component}")

runtime.stop()

print("\nRuntime Status:", runtime.status())

print("\nArcV1 Shutdown Complete")