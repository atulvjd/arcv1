"""
ArcV1 Google Gemini Model Provider

Integrates with Google Gemini API for model inference.
Requires: google-generativeai Python package and API key.
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


class GeminiProvider(BaseModel):
    """
    Provider for Google Gemini model inference.
    
    Supports Gemini Pro, Gemini Ultra and other Google models.
    Requires an API key configured in ModelConfig.
    """
    
    def __init__(self, name: str = "gemini") -> None:
        super().__init__(name)
        self._model: Any = None
    
    def load(self, config: ModelConfig) -> None:
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "google-generativeai package is required. "
                "Install with: pip install google-generativeai"
            )
        genai.configure(api_key=config.api_key or None)
        self._model = genai.GenerativeModel(
            config.model_id or "gemini-pro"
        )
        self._config = config
        self._loaded = True
    
    def unload(self) -> None:
        self._model = None
        self._loaded = False
    
    def generate(self, prompt: str, **kwargs: Any) -> ModelResult:
        if not self._loaded:
            raise RuntimeError("Model is not loaded.")
        
        import time
        start = time.time()
        
        response = self._model.generate_content(
            prompt,
            **{**self._config.parameters, **kwargs}
        )
        
        duration = (time.time() - start) * 1000
        
        return ModelResult(
            text=response.text,
            model=self._config.model_id,
            provider="gemini",
            duration_ms=duration
        )
    
    async def stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[ModelStreamChunk]:
        if not self._loaded:
            raise RuntimeError("Model is not loaded.")
        
        response = self._model.generate_content(
            prompt,
            stream=True,
            **{**self._config.parameters, **kwargs}
        )
        
        tokens = 0
        for chunk in response:
            if chunk.text:
                tokens += 1
                yield ModelStreamChunk(
                    text=chunk.text,
                    model=self._config.model_id,
                    tokens_out=tokens
                )
    
    def embeddings(self, texts: list[str]) -> list[list[float]]:
        if not self._loaded:
            raise RuntimeError("Model is not loaded.")
        
        import google.generativeai as genai
        result = genai.embed_content(
            model="embedding-001",
            content=texts
        )
        return result["embedding"]
    
    def metadata(self) -> ModelMetadata:
        return ModelMetadata(
            name=self.name,
            provider="gemini",
            model_id=self._config.model_id if self._config else "gemini-pro",
            capabilities=["generate", "stream", "embeddings"],
            version="1.0.0",
            context_length=32000
        )