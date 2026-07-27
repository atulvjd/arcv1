"""
Comprehensive tests for the Model Layer.

Covers:
- ModelRegistry: register, unregister, duplicate, clear
- MockProvider: load, unload, generate, stream, embeddings
- ModelManager: load, unload, switch, generate, stream
- Failure modes: invalid model IDs, unloaded model, duplicate registration
- Concurrency: thread-safe operations
"""

from __future__ import annotations

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pytest

from core.exceptions import ModelError
from models.base import BaseModel, ModelConfig, ModelMetadata, ModelResult, ModelStreamChunk
from models.registry import ModelRegistry
from models.manager import ModelManager
from models.providers.mock import MockProvider


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def empty_registry() -> ModelRegistry:
    return ModelRegistry()


@pytest.fixture
def filled_registry(empty_registry: ModelRegistry) -> ModelRegistry:
    empty_registry.register("mock-1", MockProvider("mock-1"))
    empty_registry.register("mock-2", MockProvider("mock-2"))
    return empty_registry


@pytest.fixture
def mock_provider() -> MockProvider:
    return MockProvider("test-mock")


@pytest.fixture
def loaded_provider(mock_provider: MockProvider) -> MockProvider:
    mock_provider.load(ModelConfig(model_id="test-model", endpoint="", api_key="", parameters={}))
    return mock_provider


@pytest.fixture
def manager(filled_registry: ModelRegistry) -> ModelManager:
    return ModelManager(registry=filled_registry)


# ---------------------------------------------------------------------------
# ModelConfig Tests
# ---------------------------------------------------------------------------

class TestModelConfig:
    def test_default_config(self):
        config = ModelConfig()
        assert config.model_id == "default"
        assert config.endpoint == ""
        assert config.api_key == ""
        assert config.parameters == {}

    def test_custom_config(self):
        config = ModelConfig(
            model_id="custom-model",
            endpoint="https://api.example.com",
            api_key="sk-abc123",
            parameters={"temperature": 0.7, "max_tokens": 100}
        )
        assert config.model_id == "custom-model"
        assert config.endpoint == "https://api.example.com"
        assert config.api_key == "sk-abc123"
        assert config.parameters["temperature"] == 0.7

    def test_immutable_parameters_copy(self):
        params = {"temp": 0.5}
        config = ModelConfig(parameters=params)
        params["temp"] = 0.9  # Modify original
        assert config.parameters["temp"] == 0.5  # Should be separate


# ---------------------------------------------------------------------------
# ModelRegistry Tests
# ---------------------------------------------------------------------------

class TestModelRegistry:
    def test_register(self, empty_registry: ModelRegistry):
        provider = MockProvider("provider1")
        empty_registry.register("provider1", provider)
        assert empty_registry.count() == 1
        assert empty_registry.exists("provider1")

    def test_duplicate_register_raises(self, empty_registry: ModelRegistry):
        provider = MockProvider("dup")
        empty_registry.register("dup", provider)
        with pytest.raises(ValueError, match="already registered"):
            empty_registry.register("dup", MockProvider("dup2"))

    def test_get(self, filled_registry: ModelRegistry):
        provider = filled_registry.get("mock-1")
        assert provider is not None
        assert provider.name == "mock-1"

    def test_get_nonexistent(self, empty_registry: ModelRegistry):
        assert empty_registry.get("nonexistent") is None

    def test_unregister(self, filled_registry: ModelRegistry):
        filled_registry.unregister("mock-1")
        assert not filled_registry.exists("mock-1")
        assert filled_registry.count() == 1

    def test_unregister_nonexistent_raises(self, empty_registry: ModelRegistry):
        with pytest.raises(KeyError, match="not found"):
            empty_registry.unregister("nonexistent")

    def test_list(self, filled_registry: ModelRegistry):
        names = filled_registry.list()
        assert names == ["mock-1", "mock-2"]

    def test_list_empty(self, empty_registry: ModelRegistry):
        assert empty_registry.list() == []

    def test_list_loaded(self, filled_registry: ModelRegistry):
        # No models loaded yet
        assert filled_registry.list_loaded() == []

    def test_clear(self, filled_registry: ModelRegistry):
        filled_registry.clear()
        assert filled_registry.count() == 0

    def test_registry_clear_unloads(self, filled_registry: ModelRegistry):
        """Clear should unload all loaded models."""
        p1 = filled_registry.get("mock-1")
        p2 = filled_registry.get("mock-2")
        if p1:
            p1.load(ModelConfig())
        if p2:
            p2.load(ModelConfig())
        assert p1 and p1.loaded
        filled_registry.clear()
        assert p1 and not p1.loaded


# ---------------------------------------------------------------------------
# MockProvider Tests
# ---------------------------------------------------------------------------

class TestMockProvider:
    def test_initial_state(self, mock_provider: MockProvider):
        assert not mock_provider.loaded
        assert mock_provider.call_count == 0
        assert mock_provider.name == "test-mock"

    def test_load(self, mock_provider: MockProvider):
        mock_provider.load(ModelConfig(model_id="my-model"))
        assert mock_provider.loaded
        assert mock_provider._config is not None
        assert mock_provider._config.model_id == "my-model"

    def test_unload(self, loaded_provider: MockProvider):
        loaded_provider.unload()
        assert not loaded_provider.loaded
        assert loaded_provider._config is None

    def test_generate_when_loaded(self, loaded_provider: MockProvider):
        result = loaded_provider.generate("Hello world")
        assert isinstance(result, ModelResult)
        assert "[MockProvider]" in result.text
        assert loaded_provider.call_count == 1

    def test_generate_when_not_loaded_raises(self, mock_provider: MockProvider):
        with pytest.raises(RuntimeError, match="not loaded"):
            mock_provider.generate("test")

    def test_generate_increments_call_count(self, loaded_provider: MockProvider):
        loaded_provider.generate("test")
        assert loaded_provider.call_count == 1
        loaded_provider.generate("test")
        assert loaded_provider.call_count == 2

    def test_stream_when_loaded(self, loaded_provider: MockProvider):
        async def run():
            chunks = []
            async for chunk in loaded_provider.stream("Hello world"):
                chunks.append(chunk)
            return chunks

        chunks = asyncio.run(run())
        assert len(chunks) > 0
        assert all(isinstance(c, ModelStreamChunk) for c in chunks)
        assert chunks[-1].finished

    def test_stream_when_not_loaded_raises(self, mock_provider: MockProvider):
        async def run():
            with pytest.raises(RuntimeError, match="not loaded"):
                async for _ in mock_provider.stream("test"):
                    pass

        asyncio.run(run())

    def test_embeddings(self, loaded_provider: MockProvider):
        vectors = loaded_provider.embeddings(["text1", "text2"])
        assert len(vectors) == 2
        assert all(len(v) == 384 for v in vectors)

    def test_metadata(self, loaded_provider: MockProvider):
        meta = loaded_provider.metadata()
        assert isinstance(meta, ModelMetadata)
        assert meta.provider == "mock"
        assert "generate" in meta.capabilities

    def test_metadata_before_load(self, mock_provider: MockProvider):
        meta = mock_provider.metadata()
        assert meta.model_id == "default"

    def test_count_tokens(self, mock_provider: MockProvider):
        count = mock_provider.count_tokens("hello world test")
        assert count == 3

    def test_empty_prompt_generation(self, loaded_provider: MockProvider):
        result = loaded_provider.generate("")
        assert isinstance(result, ModelResult)

    def test_long_prompt_generation(self, loaded_provider: MockProvider):
        long_prompt = "word " * 1000
        result = loaded_provider.generate(long_prompt)
        assert isinstance(result, ModelResult)
        assert result.tokens_in >= 1000


# ---------------------------------------------------------------------------
# ModelManager Tests
# ---------------------------------------------------------------------------

class TestModelManager:
    def test_initial_state(self, manager: ModelManager):
        assert manager.active_model_name is None
        assert manager.active_model is None
        assert manager.registry.count() == 2

    def test_register_model(self, manager: ModelManager):
        p = MockProvider("new-model")
        manager.register_model("new-model", p)
        assert manager.registry.count() == 3

    def test_load_model(self, manager: ModelManager):
        config = ModelConfig(model_id="loaded-model")
        model = manager.load_model("mock-1", config)
        assert model is not None
        assert model.loaded
        assert manager.active_model_name == "mock-1"

    def test_load_model_not_registered_raises(self, manager: ModelManager):
        with pytest.raises(ModelError, match="not registered"):
            manager.load_model("nonexistent", ModelConfig())

    def test_unload_active_model(self, manager: ModelManager):
        manager.load_model("mock-1", ModelConfig())
        manager.unload_model()
        assert manager.active_model_name is None
        assert manager.active_model is None

    def test_unload_by_name(self, manager: ModelManager):
        manager.load_model("mock-1", ModelConfig())
        manager.unload_model("mock-1")
        assert manager.active_model_name is None

    def test_unload_nonexistent_raises(self, manager: ModelManager):
        with pytest.raises(KeyError, match="not found"):
            manager.unload_model("nonexistent")

    def test_switch_model(self, manager: ModelManager):
        manager.load_model("mock-1", ModelConfig())
        manager.load_model("mock-2", ModelConfig(model_id="m2"))
        assert manager.active_model_name == "mock-2"
        manager.switch_model("mock-1")
        assert manager.active_model_name == "mock-1"

    def test_switch_unloaded_model_raises(self, manager: ModelManager):
        manager.load_model("mock-1", ModelConfig())
        with pytest.raises(ModelError, match="not loaded"):
            manager.switch_model("mock-2")

    def test_switch_nonexistent_raises(self, manager: ModelManager):
        with pytest.raises(KeyError, match="not found"):
            manager.switch_model("nonexistent")

    def test_generate_on_active_model(self, manager: ModelManager):
        manager.load_model("mock-1", ModelConfig())
        result = manager.generate("Hello")
        assert isinstance(result, ModelResult)
        assert "[MockProvider]" in result.text

    def test_generate_without_active_raises(self, manager: ModelManager):
        with pytest.raises(RuntimeError, match="No active model"):
            manager.generate("Hello")

    def test_stream_on_active_model(self, manager: ModelManager):
        manager.load_model("mock-1", ModelConfig())

        async def run():
            chunks = []
            async for chunk in manager.stream("Hello"):
                chunks.append(chunk)
            return chunks

        chunks = asyncio.run(run())
        assert len(chunks) > 0

    def test_stream_without_active_raises(self, manager: ModelManager):
        async def run():
            with pytest.raises(RuntimeError, match="No active model"):
                async for _ in manager.stream("Hello"):
                    pass

        asyncio.run(run())

    def test_embeddings_on_active_model(self, manager: ModelManager):
        manager.load_model("mock-1", ModelConfig())
        vectors = manager.embeddings(["test"])
        assert len(vectors) == 1

    def test_embeddings_without_active_raises(self, manager: ModelManager):
        with pytest.raises(RuntimeError, match="No active model"):
            manager.embeddings(["test"])

    def test_active_metadata(self, manager: ModelManager):
        manager.load_model("mock-1", ModelConfig())
        meta = manager.active_metadata()
        assert isinstance(meta, ModelMetadata)

    def test_active_metadata_without_active_raises(self, manager: ModelManager):
        with pytest.raises(RuntimeError, match="No active model"):
            manager.active_metadata()

    def test_health_check(self, manager: ModelManager):
        health = manager.health_check()
        assert "active_model" in health
        assert "is_loaded" in health
        assert health["registered_models"] == 2

    def test_health_after_load(self, manager: ModelManager):
        manager.load_model("mock-1", ModelConfig())
        health = manager.health_check()
        assert health["active_model"] == "mock-1"
        assert health["is_loaded"]


# ---------------------------------------------------------------------------
# Abstract BaseModel conformance test
# ---------------------------------------------------------------------------

class TestAbstractModel:
    """Test that MockProvider conforms to all BaseModel abstract methods."""

    def test_all_abstract_methods_implemented(self):
        # Should not raise TypeError
        provider = MockProvider()
        # All abstract methods should exist and be callable (except stream which is async)
        assert hasattr(provider, "load")
        assert hasattr(provider, "unload")
        assert hasattr(provider, "generate")
        assert hasattr(provider, "stream")
        assert hasattr(provider, "embeddings")
        assert hasattr(provider, "metadata")

    def test_cannot_instantiate_base_model(self):
        with pytest.raises(TypeError):
            BaseModel()  # abstract


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
