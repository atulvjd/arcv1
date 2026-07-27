"""
ArcV1 Configuration Manager

Hierarchical configuration with graceful fallback.
Loading priority:
1. Environment variables (ARC_ prefix)
2. Config file (config/default.json)
3. Built-in defaults

Kernel never crashes because a config file is missing.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from core.logger import get_logger


# Built-in defaults for the entire runtime
DEFAULTS: dict[str, Any] = {
    "kernel": {
        "name": "ArcV1",
        "version": "1.0.0",
        "debug": False
    },
    "models": {
        "default": {
            "provider": "mock",
            "model_id": "mock-default",
            "parameters": {
                "temperature": 0.7,
                "max_tokens": 1024
            }
        }
    },
    "tools": {
        "filesystem": {
            "enabled": True,
            "allowed_paths": None
        },
        "terminal": {
            "enabled": True,
            "allowed_commands": None
        }
    },
    "scheduler": {
        "poll_interval": 0.1,
        "max_concurrent": 4
    },
}


class Config:
    """
    Configuration manager for ArcV1.

    Gracefully falls back to built-in defaults if no config file exists.
    Environment variables with ARC_ prefix override file values.
    """

    def __init__(self, config_path: str | None = None) -> None:
        """
        Initialize configuration.

        Args:
            config_path: Optional path to JSON config file.
                         Defaults to config/default.json.
        """
        self.logger = get_logger("Config")
        self._config: dict[str, Any] = {}
        self._config_path = config_path or "config/default.json"
        self._load()

    def _load(self) -> None:
        """Load configuration from file, then allow env overrides."""
        # Start with built-in defaults
        self._config = dict(DEFAULTS)

        # Try to load from file
        path = Path(self._config_path)
        if path.exists():
            try:
                with path.open("r", encoding="utf-8") as f:
                    file_config = json.load(f)
                self._merge(file_config)
                self.logger.debug(f"Loaded config from {self._config_path}")
            except Exception as e:
                self.logger.warning(f"Failed to load config file: {e}")
        else:
            self.logger.info(f"Config file not found at {self._config_path}, using defaults.")

        # Apply environment variable overrides
        self._apply_env_overrides()

    def _merge(self, overlay: dict[str, Any], target: dict[str, Any] | None = None) -> None:
        """Deep merge overlay dict into target dict."""
        target = target or self._config
        for key, value in overlay.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge(value, target[key])
            else:
                target[key] = value

    def _apply_env_overrides(self) -> None:
        """Apply ARC_ prefixed environment variables."""
        prefix = "ARC_"
        for env_key, env_value in os.environ.items():
            if env_key.startswith(prefix):
                config_key = env_key[len(prefix):].lower().replace("__", ".")
                self._config[config_key] = env_value
                self.logger.debug(f"Env override: {config_key} = {env_value}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by dot-notation key.

        Supports nested keys like 'models.default.model_id'.
        Falls back to simple key access.

        Args:
            key: Dot-separated key path or simple key.
            default: Value to return if key not found.

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
        """Return a deep copy of all configuration."""
        return json.loads(json.dumps(self._config))
