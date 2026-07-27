from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class Config:
    """Configuration manager for ArcV1."""

    def __init__(self, config_path: str = "config/default.json") -> None:
        self._config: dict[str, Any] = {}
        self._config_path = config_path
        self.load(config_path)

    def load(self, config_path: str) -> None:
        path = Path(config_path)

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with path.open("r", encoding="utf-8") as file:
            self._config = json.load(file)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by dot-notation key.
        
        Supports nested keys like 'models.default.model_id'.
        Falls back to single-level key access for backward compatibility.
        
        Args:
            key: Dot-separated key path or simple key.
            default: Default value if key not found.
            
        Returns:
            The configuration value, or default.
        """
        if '.' in key:
            parts = key.split('.')
            current = self._config
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                    if current is None:
                        return default
                else:
                    return default
            return current
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._config[key] = value

    def all(self) -> dict[str, Any]:
        """Return a copy of all configuration."""
        return self._config.copy()