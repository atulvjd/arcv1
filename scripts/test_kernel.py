from core.kernel import Kernel

kernel = Kernel()


def on_boot():
    print(">> Event: Kernel Boot")


def on_shutdown():
    print(">> Event: Kernel Shutdown")


kernel.events.subscribe("kernel.boot", on_boot)
kernel.events.subscribe("kernel.shutdown", on_shutdown)

kernel.boot()

print(f"Running: {kernel.running}")

kernel.shutdown()

print(f"Running: {kernel.running}")