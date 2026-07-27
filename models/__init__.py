"""
ArcV1 Model Layer

Abstract interfaces and management for model providers.
LLMService communicates exclusively through BaseModel.

All providers in models/providers/ implement BaseModel.
"""

from models.base import (
    BaseModel,
    ModelConfig,
    ModelMetadata,
    ModelResult,
    ModelStreamChunk,
)
from models.manager import ModelManager
from models.registry import ModelRegistry

__all__ = [
    "BaseModel",
    "ModelConfig",
    "ModelMetadata",
    "ModelResult",
    "ModelStreamChunk",
    "ModelManager",
    "ModelRegistry",
]