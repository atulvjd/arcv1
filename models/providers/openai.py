"""
ArcV1 OpenAI Model Provider

Integrates with OpenAI API for model inference.
Requires: openai Python package and API key.
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


class OpenAIProvider(BaseModel):
    """
    Provider for OpenAI model inference.
    
    Supports GPT-4, GPT-3.5, and other OpenAI models.
    Requires an API key configured in ModelConfig.
    """
    
    def __init__(self, name: str = "openai") -> None:
        super().__init__(name)
        self._client: Any = None
    
    def load(self, config: ModelConfig) -> None:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package is required. Install with: pip install openai"
            )
        self._client = OpenAI(api_key=config.api_key or None)
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
        
        response = self._client.chat.completions.create(
            model=self._config.model_id,
            messages=[{"role": "user", "content": prompt}],
            **{**self._config.parameters, **kwargs}
        )
        
        duration = (time.time() - start) * 1000
        choice = response.choices[0]
        
        return ModelResult(
            text=choice.message.content or "",
            model=self._config.model_id,
            provider="openai",
            tokens_in=response.usage.prompt_tokens if response.usage else 0,
            tokens_out=response.usage.completion_tokens if response.usage else 0,
            duration_ms=duration
        )
    
    async def stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[ModelStreamChunk]:
        if not self._loaded:
            raise RuntimeError("Model is not loaded.")
        
        stream = self._client.chat.completions.create(
            model=self._config.model_id,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            **{**self._config.parameters, **kwargs}
        )
        
        tokens = 0
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                tokens += 1
                yield ModelStreamChunk(
                    text=chunk.choices[0].delta.content,
                    finished=chunk.choices[0].finish_reason is not None,
                    model=self._config.model_id,
                    tokens_out=tokens
                )
    
    def embeddings(self, texts: list[str]) -> list[list[float]]:
        if not self._loaded:
            raise RuntimeError("Model is not loaded.")
        
        response = self._client.embeddings.create(
            model=self._config.parameters.get("embedding_model", "text-embedding-3-small"),
            input=texts
        )
        return [item.embedding for item in response.data]
    
    def metadata(self) -> ModelMetadata:
        return ModelMetadata(
            name=self.name,
            provider="openai",
            model_id=self._config.model_id if self._config else "gpt-4",
            capabilities=["generate", "stream", "embeddings"],
            version="1.0.0",
            context_length=128000
        )