"""Test Kernel boot and shutdown with services."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
print(f"Services: {list(kernel.services.keys())}")

# Test getting a service
llm_service = kernel.get_service("llm")
print(f"LLM Service: {llm_service.name}")
print(f"LLM Service State: {llm_service.state.value}")

memory_service = kernel.get_service("memory")
print(f"Memory Service: {memory_service.name}")
print(f"Memory Service State: {memory_service.state.value}")

kernel.shutdown()

print(f"Running: {kernel.running}")