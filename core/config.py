from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class Config:
    """Configuration manager for ArcV1."""

    def __init__(self, config_path: str = "config/default.json") -> None:
        self._config: dict[str, Any] = {}
        self.load(config_path)

    def load(self, config_path: str) -> None:
        path = Path(config_path)

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with path.open("r", encoding="utf-8") as file:
            self._config = json.load(file)

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._config[key] = value

    def all(self) -> dict[str, Any]:
        return self._config.copy()