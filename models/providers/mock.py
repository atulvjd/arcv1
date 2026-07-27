"""\"\"\"
ArcV1 Mock Model Provider

Returns placeholder responses for testing and development.
No external dependencies required.
\"\"\"

from __future__ import annotations

import time
from typing import Any, AsyncIterator

from models.base import (
    BaseModel,
    ModelConfig,
    ModelMetadata,
    ModelResult,
    ModelStreamChunk,
)


class MockProvider(BaseModel):
    \"\"\"
    Mock model provider for testing and development.

    Returns predictable responses without any external API calls.
    Useful for testing agents, services, and workflows offline.
    \"\"\"

    def __init__(self, name: str = \"mock\") -> None:
        \"\"\"
        Initialize the mock provider.

        Args:
            name: Provider name.
        \"\"\"
        super().__init__(name)
        self._call_count: int = 0
        self._config: ModelConfig | None = None

    def load(self, config: ModelConfig) -> None:
        \"\"\"
        Load the mock model.

        Always succeeds. Stores config for reference.

        Args:
            config: Model configuration.
        \"\"\"
        self._config = config
        self._loaded = True

    def unload(self) -> None:
        \"\"\"Unload the mock model.\"\"\"
        self._loaded = False
        self._config = None

    def generate(self, prompt: str, **kwargs: Any) -> ModelResult:
        \"\"\"
        Generate a mock response.

        Args:
            prompt: Input prompt (first 50 chars used).
            **kwargs: Additional parameters (ignored).

        Returns:
            ModelResult with placeholder text.
        \"\"\"
        if not self._loaded:
            raise RuntimeError(\"Model is not loaded.\")

        self._call_count += 1
        start = time.time()

        text = f\"[MockProvider] Response to: {prompt[:50]}...\"

        duration = (time.time() - start) * 1000

        meta = self.metadata()
        return ModelResult(
            text=text,
            model=meta.model_id,
            provider=meta.provider,
            tokens_in=len(prompt.split()),
            tokens_out=len(text.split()),
            duration_ms=duration
        )

    async def stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[ModelStreamChunk]:
        \"\"\"
        Stream a mock response word by word.

        Args:
            prompt: Input prompt.
            **kwargs: Additional parameters.

        Yields:
            ModelStreamChunk for each word.
        \"\"\"
        result = self.generate(prompt, **kwargs)
        words = result.text.split(\" \")
        total = len(words)

        for i, word in enumerate(words):
            yield ModelStreamChunk(
                text=word + \" \",
                finished=(i == total - 1),
                model=self.name,
                tokens_out=i + 1
            )

    def embeddings(self, texts: list[str]) -> list[list[float]]:
        \"\"\"Return mock embedding vectors.\"\"\"
        return [[0.1] * 384 for _ in texts]

    def metadata(self) -> ModelMetadata:
        \"\"\"Return metadata about this mock provider.\"\"\"
        return ModelMetadata(
            name=self.name,
            provider=\"mock\",
            model_id=self._config.model_id if self._config else \"default\",
            capabilities=[\"generate\", \"stream\", \"embeddings\"],
            version=\"1.0.0\",
            context_length=8192
        )

    @property
    def call_count(self) -> int:
        \"\"\"Number of generate() calls made.\"\"\"
        return self._call_count"""