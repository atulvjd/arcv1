"""
ArcV1 Runtime

Public API for controlling the ArcV1 Kernel.
"""

from __future__ import annotations

from core.kernel import Kernel


class Runtime:
    """ArcV1 Runtime Controller."""

    def __init__(self) -> None:
        self.kernel = Kernel()

    def start(self) -> None:
        """Start the runtime."""
        self.kernel.boot()

    def stop(self) -> None:
        """Stop the runtime."""
        self.kernel.shutdown()

    def restart(self) -> None:
        """Restart the runtime."""
        self.stop()
        self.start()

    def status(self) -> bool:
        """Return runtime status."""
        return self.kernel.running