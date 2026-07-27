"""
ArcV1 HuggingFace Model Provider

Integrates with HuggingFace Inference API or local transformers.
Requires: transformers or requests Python package.
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


class HuggingFaceProvider(BaseModel):
    """
    Provider for HuggingFace model inference.
    
    Supports both local transformers models and
    HuggingFace Inference API.
    """
    
    def __init__(self, name: str = "huggingface") -> None:
        super().__init__(name)
        self._pipeline: Any = None
        self._api_token: str = ""
    
    def load(self, config: ModelConfig) -> None:
        self._config = config
        self._api_token = config.api_key or ""
        
        if config.endpoint:
            # Use Inference API
            self._use_api = True
        else:
            # Use local transformers
            try:
                from transformers import pipeline
                self._pipeline = pipeline(
                    "text-generation",
                    model=config.model_id
                )
            except ImportError:
                raise ImportError(
                    "transformers package is required for local models. "
                    "Install with: pip install transformers"
                )
            self._use_api = False
        
        self._loaded = True
    
    def unload(self) -> None:
        self._pipeline = None
        self._loaded = False
    
    def generate(self, prompt: str, **kwargs: Any) -> ModelResult:
        if not self._loaded:
            raise RuntimeError("Model is not loaded.")
        
        import time
        start = time.time()
        
        if self._use_api:
            import requests
            headers = {"Authorization": f"Bearer {self._api_token}"}
            response = requests.post(
                f"{self._config.endpoint}",
                headers=headers,
                json={
                    "inputs": prompt,
                    "parameters": {**self._config.parameters, **kwargs}
                }
            )
            text = response.json()[0]["generated_text"]
        else:
            result = self._pipeline(
                prompt,
                **{**self._config.parameters, **kwargs}
            )
            text = result[0]["generated_text"]
        
        duration = (time.time() - start) * 1000
        
        return ModelResult(
            text=text,
            model=self._config.model_id,
            provider="huggingface",
            duration_ms=duration
        )
    
    async def stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[ModelStreamChunk]:
        result = self.generate(prompt, **kwargs)
        words = result.text.split(" ")
        total = len(words)
        for i, word in enumerate(words):
            yield ModelStreamChunk(
                text=word + " ",
                finished=(i == total - 1),
                model=self._config.model_id,
                tokens_out=i + 1
            )
    
    def metadata(self) -> ModelMetadata:
        return ModelMetadata(
            name=self.name,
            provider="huggingface",
            model_id=self._config.model_id if self._config else "default",
            capabilities=["generate", "stream"],
            version="1.0.0",
            context_length=2048
        )