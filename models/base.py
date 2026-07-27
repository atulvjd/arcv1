"""
ArcV1 Model Layer

Defines the abstract interface for all model providers.
LLMService communicates exclusively through BaseModel.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator


@dataclass
class ModelConfig:
    """
    Configuration for loading a model provider.
    
    Attributes:
        model_id: Provider-specific model identifier.
        endpoint: API endpoint URL.
        api_key: Authentication key (if required).
        parameters: Default generation parameters.
    """
    model_id: str = "default"
    endpoint: str = ""
    api_key: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelMetadata:
    """
    Metadata describing a loaded model.
    
    Attributes:
        name: Model name.
        provider: Provider name (e.g., 'ollama', 'openai').
        model_id: Provider-specific model identifier.
        capabilities: List of supported features.
        version: Model version.
        context_length: Maximum context window size.
    """
    name: str
    provider: str
    model_id: str = "default"
    capabilities: list[str] = field(default_factory=list)
    version: str = "1.0.0"
    context_length: int = 4096


@dataclass
class ModelResult:
    """
    Result from a model generation.
    
    Attributes:
        text: Generated text output.
        model: Name of the model used.
        provider: Provider name.
        tokens_in: Input token count.
        tokens_out: Output token count.
        duration_ms: Generation time in milliseconds.
    """
    text: str
    model: str = ""
    provider: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    duration_ms: float = 0.0


@dataclass
class ModelStreamChunk:
    """
    A single chunk from a streaming generation.
    
    Attributes:
        text: Text content of this chunk.
        finished: Whether generation is complete.
        model: Model name.
        tokens_in: Total input tokens (sent on last chunk).
        tokens_out: Total output tokens so far.
    """
    text: str
    finished: bool = False
    model: str = ""
    tokens_in: int = 0
    tokens_out: int = 0


class BaseModel(ABC):
    """
    Abstract interface for all model providers.
    
    Every model provider must implement this interface.
    LLMService communicates ONLY through BaseModel.
    """
    
    def __init__(self, name: str = "base_model") -> None:
        """
        Initialize the model.
        
        Args:
            name: A human-readable name for this model instance.
        """
        self.name = name
        self._loaded: bool = False
        self._config: ModelConfig | None = None
    
    @property
    def loaded(self) -> bool:
        """Check if the model is currently loaded."""
        return self._loaded
    
    @abstractmethod
    def load(self, config: ModelConfig) -> None:
        """
        Load the model with the given configuration.
        
        Args:
            config: Configuration for loading this model.
            
        Raises:
            ModelError: If loading fails.
        """
        ...
    
    @abstractmethod
    def unload(self) -> None:
        """
        Unload the model and free resources.
        """
        ...
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> ModelResult:
        """
        Generate text from a prompt.
        
        Args:
            prompt: The input prompt string.
            **kwargs: Additional generation parameters.
            
        Returns:
            ModelResult containing generated text and metadata.
            
        Raises:
            ModelError: If generation fails.
            RuntimeError: If model is not loaded.
        """
        ...
    
    @abstractmethod
    async def stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[ModelStreamChunk]:
        """
        Stream generated text token by token.
        
        Args:
            prompt: The input prompt string.
            **kwargs: Additional generation parameters.
            
        Yields:
            ModelStreamChunk for each token/segment.
            
        Raises:
            ModelError: If generation fails.
            RuntimeError: If model is not loaded.
        """
        ...
    
    @abstractmethod
    def embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for the given texts.
        
        This is future-ready. Default implementations should raise
        NotImplementedError with a clear message.
        
        Args:
            texts: List of input texts to embed.
            
        Returns:
            List of embedding vectors.
        """
        raise NotImplementedError(
            f"Embeddings not supported by {self.__class__.__name__}"
        )
    
    @abstractmethod
    def metadata(self) -> ModelMetadata:
        """
        Return metadata about this model.
        
        Returns:
            ModelMetadata describing capabilities and configuration.
        """
        ...
    
    def count_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in text.
        
        Default implementation uses a simple word-count heuristic.
        Providers should override with accurate tokenizers.
        
        Args:
            text: Input text.
            
        Returns:
            Estimated token count.
        """
        return len(text.split())