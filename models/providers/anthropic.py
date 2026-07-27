"""
ArcV1 Anthropic Model Provider

Integrates with Anthropic API for Claude model inference.
Requires: anthropic Python package and API key.
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


class AnthropicProvider(BaseModel):
    """
    Provider for Anthropic Claude model inference.
    
    Supports Claude 3 Opus, Sonnet, Haiku and other Anthropic models.
    Requires an API key configured in ModelConfig.
    """
    
    def __init__(self, name: str = "anthropic") -> None:
        super().__init__(name)
        self._client: Any = None
    
    def load(self, config: ModelConfig) -> None:
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "anthropic package is required. Install with: pip install anthropic"
            )
        self._client = anthropic.Anthropic(api_key=config.api_key or None)
        self._config = config
        self._loaded = True
    
    def unload(self) -> None:
        self._client = None
        self._loaded = False
    
    def generate(self, prompt: str, **kwargs: Any) -> ModelResult:
        if not self._loaded:
            raise RuntimeError("Model is not loaded.")
        
        import time
        start = time.time()
        
        response = self._client.messages.create(
            model=self._config.model_id,
            max_tokens=self._config.parameters.get("max_tokens", 4096),
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        
        duration = (time.time() - start) * 1000
        
        return ModelResult(
            text=response.content[0].text,
            model=self._config.model_id,
            provider="anthropic",
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            duration_ms=duration
        )
    
    async def stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[ModelStreamChunk]:
        if not self._loaded:
            raise RuntimeError("Model is not loaded.")
        
        with self._client.messages.stream(
            model=self._config.model_id,
            max_tokens=self._config.parameters.get("max_tokens", 4096),
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        ) as stream:
            tokens = 0
            for text_chunk in stream.text_stream:
                tokens += 1
                yield ModelStreamChunk(
                    text=text_chunk,
                    model=self._config.model_id,
                    tokens_out=tokens
                )
    
    def metadata(self) -> ModelMetadata:
        return ModelMetadata(
            name=self.name,
            provider="anthropic",
            model_id=self._config.model_id if self._config else "claude-3-opus-20240229",
            capabilities=["generate", "stream"],
            version="1.0.0",
            context_length=200000
        )