"""
ArcV1 Ollama Model Provider

Integrates with local Ollama instances for model inference.
Requires: ollama Python package or HTTP API access.
"""

from __future__ import annotations

from typing import Any, AsyncIterator

from models.base import (
    BaseModel,
    ModelConfig,
    ModelMetadata,
    ModelResult,
    ModelStreamChunk,
)


class OllamaProvider(BaseModel):
    """
    Provider for local Ollama model inference.
    
    Connects to a running Ollama instance at the configured endpoint.
    Supports all Ollama-compatible models.
    """
    
    def __init__(self, name: str = "ollama") -> None:
        """
        Initialize the Ollama provider.
        
        Args:
            name: Provider name.
        """
        super().__init__(name)
        self._client: Any = None
    
    def load(self, config: ModelConfig) -> None:
        """
        Connect to Ollama instance.
        
        Args:
            config: Configuration with endpoint and model_id.
        """
        try:
            import ollama  # type: ignore
        except ImportError:
            raise ImportError(
                "ollama package is required. Install with: pip install ollama"
            )
        
        host = config.endpoint or "http://localhost:11434"
        self._client = ollama.Client(host=host)
        self._config = config
        self._loaded = True
    
    def unload(self) -> None:
        """Disconnect from Ollama instance."""
        self._client = None
        self._loaded = False
    
    def generate(self, prompt: str, **kwargs: Any) -> ModelResult:
        """
        Generate text using Ollama.
        
        Args:
            prompt: Input prompt.
            **kwargs: Override generation parameters.
            
        Returns:
            ModelResult with generated text.
        """
        if not self._loaded:
            raise RuntimeError("Model is not loaded.")
        
        import time
        start = time.time()
        
        response = self._client.generate(
            model=self._config.model_id,
            prompt=prompt,
            **{**self._config.parameters, **kwargs}
        )
        
        duration = (time.time() - start) * 1000
        
        return ModelResult(
            text=response["response"],
            model=self._config.model_id,
            provider="ollama",
            tokens_in=response.get("prompt_eval_count", 0),
            tokens_out=response.get("eval_count", 0),
            duration_ms=duration
        )
    
    async def stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[ModelStreamChunk]:
        """
        Stream text from Ollama.
        
        Args:
            prompt: Input prompt.
            **kwargs: Override generation parameters.
            
        Yields:
            ModelStreamChunk for each token.
        """
        if not self._loaded:
            raise RuntimeError("Model is not loaded.")
        
        stream = self._client.generate(
            model=self._config.model_id,
            prompt=prompt,
            stream=True,
            **{**self._config.parameters, **kwargs}
        )
        
        tokens = 0
        for chunk in stream:
            tokens += 1
            yield ModelStreamChunk(
                text=chunk["response"],
                finished=chunk.get("done", False),
                model=self._config.model_id,
                tokens_out=tokens
            )
    
    def embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings using Ollama.
        
        Args:
            texts: Input texts.
            
        Returns:
            List of embedding vectors.
        """
        if not self._loaded:
            raise RuntimeError("Model is not loaded.")
        
        return [
            self._client.embeddings(
                model=self._config.model_id,
                prompt=text
            )["embedding"]
            for text in texts
        ]
    
    def metadata(self) -> ModelMetadata:
        """Return metadata about the Ollama model."""
        return ModelMetadata(
            name=self.name,
            provider="ollama",
            model_id=self._config.model_id if self._config else "default",
            capabilities=["generate", "stream", "embeddings"],
            version="1.0.0",
            context_length=8192
        )