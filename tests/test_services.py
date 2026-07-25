"""
Comprehensive tests for ArcV1 Service Layer.

Tests all services including LLM, Memory, Prompt, Tool, and Router.
"""

from __future__ import annotations

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.base import BaseService, ServiceState
from services.llm import LLMService, BaseLLMBackend, MockLLMBackend
from services.memory import MemoryService, MemoryBackend, InMemoryBackend
from services.prompt import PromptService, PromptTemplate
from services.router import RouterService
from services.tool import (
    ToolService,
    BaseTool,
    MockTool,
    ToolCategory,
    ToolMetadata,
    ToolParameter,
)


class TestResult:
    """Helper to track test results."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def check(self, condition: bool, message: str) -> None:
        if condition:
            self.passed += 1
            print(f"  ✓ {message}")
        else:
            self.failed += 1
            self.errors.append(message)
            print(f"  ✗ {message}")
    
    def summary(self) -> str:
        total = self.passed + self.failed
        return f"\n{'='*50}\nResults: {self.passed}/{total} passed\n{'='*50}"


def test_service_state():
    """Test ServiceState enum."""
    print("\n[Testing ServiceState]")
    results = TestResult()
    
    results.check(ServiceState.CREATED.value == "created", "CREATED state exists")
    results.check(ServiceState.RUNNING.value == "running", "RUNNING state exists")
    results.check(ServiceState.STOPPED.value == "stopped", "STOPPED state exists")
    results.check(ServiceState.ERROR.value == "error", "ERROR state exists")
    
    print(results.summary())
    return results


def test_base_service():
    """Test BaseService lifecycle."""
    print("\n[Testing BaseService]")
    results = TestResult()
    
    # Create a concrete implementation for testing
    class TestService(BaseService):
        def __init__(self, name="TestService"):
            super().__init__(name)
            self.init_called = False
            self.start_called = False
            self.stop_called = False
        
        def on_initialize(self):
            self.init_called = True
        
        def on_start(self):
            self.start_called = True
        
        def on_stop(self):
            self.stop_called = True
    
    service = TestService()
    
    # Test initial state
    results.check(service.state == ServiceState.CREATED, "Initial state is CREATED")
    results.check(service.is_running == False, "Not running initially")
    
    # Test lifecycle
    service.initialize()
    results.check(service.state == ServiceState.INITIALIZED, "After init: INITIALIZED")
    results.check(service.init_called, "on_initialize was called")
    
    service.start()
    results.check(service.state == ServiceState.RUNNING, "After start: RUNNING")
    results.check(service.is_running, "is_running returns True")
    results.check(service.start_called, "on_start was called")
    
    service.stop()
    results.check(service.state == ServiceState.STOPPED, "After stop: STOPPED")
    results.check(service.is_running == False, "is_running returns False")
    results.check(service.stop_called, "on_stop was called")
    
    # Test health check
    health = service.health_check()
    results.check(health["service"] == "TestService", "Health check includes service name")
    results.check(health["state"] == "stopped", "Health check includes state")
    
    # Test configuration
    service2 = TestService("ConfigService")
    service2.configure({"key": "value"})
    results.check(service2._config == {"key": "value"}, "Configuration stored correctly")
    
    print(results.summary())
    return results


def test_llm_service():
    """Test LLMService with MockLLMBackend."""
    print("\n[Testing LLMService]")
    results = TestResult()
    
    service = LLMService("TestLLM")
    
    # Test initial state
    results.check(service.backend is None, "No backend initially")
    
    # Test lifecycle
    service.initialize()
    service.start()
    results.check(service.is_running, "Service is running")
    results.check(service.state == ServiceState.RUNNING, "State is RUNNING")
    
    # Test without backend - should raise
    try:
        service.generate("test prompt")
        results.check(False, "Should raise RuntimeError without backend")
    except RuntimeError:
        results.check(True, "Raises RuntimeError without backend")
    
    # Load mock backend
    mock_backend = MockLLMBackend("test_mock")
    service.load_backend(mock_backend)
    results.check(service.backend is not None, "Backend loaded")
    results.check(service.backend.name == "test_mock", "Backend name correct")
    
    # Test generation
    response = service.generate("Hello, world!")
    results.check("[MockLLM]" in response, "Generate returns mock response")
    results.check(mock_backend.call_count == 1, "Call count incremented")
    
    # Test unload
    service.unload_backend()
    results.check(service.backend is None, "Backend unloaded")
    
    # Test health check
    service.load_backend(MockLLMBackend("health_test"))
    health = service.health_check()
    results.check("backend" in health, "Health check includes backend")
    results.check(health["backend"]["backend"] == "health_test", "Backend health correct")
    
    service.stop()
    
    print(results.summary())
    return results


def test_memory_service():
    """Test MemoryService with InMemoryBackend."""
    print("\n[Testing MemoryService]")
    results = TestResult()
    
    service = MemoryService("TestMemory")
    
    # Test lifecycle
    service.initialize()
    service.start()
    results.check(service.is_running, "Service is running")
    
    # Test remember/recall
    service.remember("greeting", "Hello!")
    results.check(service.recall("greeting") == "Hello!", "Remember and recall work")
    
    # Test has
    results.check(service.has("greeting"), "has returns True for existing key")
    results.check(not service.has("nonexistent"), "has returns False for missing key")
    
    # Test count
    results.check(service.count() == 1, "Count is correct")
    
    # Test list_keys
    results.check(service.list_keys() == ["greeting"], "list_keys returns correct keys")
    
    # Test forget
    result = service.forget("greeting")
    results.check(result == True, "forget returns True for existing key")
    results.check(service.recall("greeting") is None, "Key no longer exists")
    
    # Test clear
    service.remember("a", 1)
    service.remember("b", 2)
    service.clear()
    results.check(service.count() == 0, "clear removes all items")
    
    # Test custom backend
    class DictBackend(MemoryBackend):
        def __init__(self):
            self._data = {}
        
        def get(self, key: str):
            return self._data.get(key)
        
        def set(self, key: str, value):
            self._data[key] = value
        
        def delete(self, key: str) -> bool:
            if key in self._data:
                del self._data[key]
                return True
            return False
        
        def exists(self, key: str) -> bool:
            return key in self._data
        
        def clear(self):
            self._data.clear()
        
        def keys(self):
            return list(self._data.keys())
        
        def count(self):
            return len(self._data)
    
    custom_backend = DictBackend()
    service.load_backend(custom_backend)
    service.remember("custom", "value")
    results.check(service.recall("custom") == "value", "Custom backend works")
    
    service.stop()
    
    print(results.summary())
    return results


def test_prompt_service():
    """Test PromptService with PromptTemplate."""
    print("\n[Testing PromptService]")
    results = TestResult()
    
    service = PromptService("TestPrompt")
    
    # Test lifecycle
    service.initialize()
    service.start()
    results.check(service.is_running, "Service is running")
    
    # Test template creation
    template = PromptTemplate(
        name="greeting",
        template="Hello, {name}! Welcome to {place}.",
        description="A greeting template",
        version="1.0.0"
    )
    
    results.check(template.name == "greeting", "Template name correct")
    results.check(template.version == "1.0.0", "Template version correct")
    results.check(sorted(template.variables) == ["name", "place"], "Variables extracted")
    
    # Test rendering
    rendered = template.render(name="Alice", place="ArcV1")
    results.check(rendered == "Hello, Alice! Welcome to ArcV1.", "Template renders correctly")
    
    # Test missing variables
    try:
        template.render(name="Alice")
        results.check(False, "Should raise ValueError for missing variables")
    except ValueError:
        results.check(True, "Raises ValueError for missing variables")
    
    # Test default variables
    template_with_defaults = PromptTemplate(
        name="defaulted",
        template="Hello, {name}! {greeting}",
        default_vars={"greeting": "How are you?"}
    )
    rendered = template_with_defaults.render(name="Bob")
    results.check("How are you?" in rendered, "Default variables work")
    
    # Test service registration
    service.register(template)
    results.check(service.exists("greeting"), "Template registered")
    results.check(service.count() == 1, "Count is correct")
    results.check("greeting" in service.list_templates(), "list_templates works")
    
    # Test service render
    result = service.render("greeting", name="Charlie", place="World")
    results.check("Charlie" in result, "Service render works")
    
    # Test unregister
    service.unregister("greeting")
    results.check(not service.exists("greeting"), "Template unregistered")
    
    # Test clear
    service.register(template)
    service.clear()
    results.check(service.count() == 0, "clear works")
    
    service.stop()
    
    print(results.summary())
    return results


def test_tool_service():
    """Test ToolService with MockTool."""
    print("\n[Testing ToolService]")
    results = TestResult()
    
    service = ToolService("TestTool")
    
    # Test lifecycle
    service.initialize()
    service.start()
    results.check(service.is_running, "Service is running")
    
    # Test tool creation
    tool = MockTool(name="test_mock", description="A test tool")
    results.check(tool.name == "test_mock", "Tool name correct")
    results.check(tool.metadata.description == "A test tool", "Tool description correct")
    
    # Test tool execution
    result = tool.execute(param1="value1")
    results.check(result["tool"] == "test_mock", "Execution returns correct tool name")
    results.check(result["params"]["param1"] == "value1", "Parameters passed correctly")
    results.check(result["execution_count"] == 1, "Execution count incremented")
    
    # Test tool health check
    health = tool.health_check()
    results.check(health["tool"] == "test_mock", "Health check includes tool name")
    results.check(health["status"] == "ok", "Health check status is ok")
    
    # Test service registration
    service.register(tool)
    results.check(service.exists("test_mock"), "Tool registered")
    results.check(service.count() == 1, "Count is correct")
    results.check("test_mock" in service.list_tools(), "list_tools works")
    
    # Test service execution
    result = service.execute("test_mock", param1="test")
    results.check(result["tool"] == "test_mock", "Service execute works")
    
    # Test list by category
    results.check(service.list_by_category(ToolCategory.CUSTOM) == ["test_mock"], "list_by_category works")
    
    # Test tool not found
    try:
        service.execute("nonexistent")
        results.check(False, "Should raise KeyError for missing tool")
    except KeyError:
        results.check(True, "Raises KeyError for missing tool")
    
    # Test unregister
    service.unregister("test_mock")
    results.check(not service.exists("test_mock"), "Tool unregistered")
    
    service.stop()
    
    print(results.summary())
    return results


def test_router_service():
    """Test RouterService."""
    print("\n[Testing RouterService]")
    results = TestResult()
    
    service = RouterService("TestRouter")
    
    # Test lifecycle
    service.initialize()
    service.start()
    results.check(service.is_running, "Service is running")
    
    # Test route registration
    def handle_chat(**kwargs):
        return {"type": "chat", **kwargs}
    
    def handle_execute(**kwargs):
        return {"type": "execute", **kwargs}
    
    service.register_route("chat", handle_chat)
    service.register_route("execute", handle_execute)
    results.check(service.exists("chat"), "Route 'chat' registered")
    results.check(service.exists("execute"), "Route 'execute' registered")
    results.check(service.count() == 2, "Count is correct")
    results.check(sorted(service.list_routes()) == ["chat", "execute"], "list_routes works")
    
    # Test routing
    result = service.route("chat", message="Hello!")
    results.check(result["type"] == "chat", "Route 'chat' works")
    results.check(result["message"] == "Hello!", "Parameters passed through")
    
    result = service.route("execute", command="ls")
    results.check(result["type"] == "execute", "Route 'execute' works")
    
    # Test no route found
    try:
        service.route("nonexistent")
        results.check(False, "Should raise KeyError for missing route")
    except KeyError:
        results.check(True, "Raises KeyError for missing route")
    
    # Test fallback
    def fallback_handler(request_type, **kwargs):
        return {"type": "fallback", "requested": request_type, **kwargs}
    
    service.set_fallback(fallback_handler)
    result = service.route("nonexistent")
    results.check(result["type"] == "fallback", "Fallback handler invoked")
    results.check(result["requested"] == "nonexistent", "Fallback receives request type")
    
    # Test unregister
    service.unregister_route("chat")
    results.check(not service.exists("chat"), "Route unregistered")
    
    # Test clear
    service.clear()
    results.check(service.count() == 0, "clear works")
    results.check(service._fallback is None, "Fallback cleared")
    
    # Test health check
    service.register_route("test", handle_chat)
    health = service.health_check()
    results.check(health["route_count"] == 1, "Health check includes route count")
    results.check(health["has_fallback"] == False, "Health check includes fallback status")
    
    service.stop()
    
    print(results.summary())
    return results


def test_async_llm_generation():
    """Test async generation with MockLLMBackend."""
    print("\n[Testing Async LLM Generation]")
    results = TestResult()
    
    async def run_async_test():
        backend = MockLLMBackend("async_test")
        
        chunks = []
        async for chunk in backend.generate_stream("Test prompt"):
            chunks.append(chunk)
        
        results.check(len(chunks) > 0, "Async stream yields chunks")
        results.check(all(isinstance(c, str) for c in chunks), "All chunks are strings")
    
    asyncio.run(run_async_test())
    
    print(results.summary())
    return results


def test_tool_parameter():
    """Test ToolParameter and ToolMetadata."""
    print("\n[Testing ToolParameter and ToolMetadata]")
    results = TestResult()
    
    param = ToolParameter(
        name="query",
        type_name="str",
        description="The search query",
        required=True
    )
    
    param_dict = param.to_dict()
    results.check(param_dict["name"] == "query", "Parameter name in dict")
    results.check(param_dict["type"] == "str", "Parameter type in dict")
    results.check(param_dict["required"] == True, "Parameter required flag in dict")
    
    metadata = ToolMetadata(
        name="search",
        description="Search tool",
        category=ToolCategory.SEARCH,
        parameters=[param],
        version="2.0.0"
    )
    
    meta_dict = metadata.to_dict()
    results.check(meta_dict["name"] == "search", "Metadata name in dict")
    results.check(meta_dict["category"] == "search", "Metadata category in dict")
    results.check(meta_dict["version"] == "2.0.0", "Metadata version in dict")
    results.check(len(meta_dict["parameters"]) == 1, "Parameters in metadata dict")
    
    print(results.summary())
    return results


def run_all_tests():
    """Run all service tests."""
    print("\n" + "="*60)
    print("ArcV1 Service Layer Test Suite")
    print("="*60)
    
    all_results = []
    
    # Run all tests
    all_results.append(test_service_state())
    all_results.append(test_base_service())
    all_results.append(test_llm_service())
    all_results.append(test_memory_service())
    all_results.append(test_prompt_service())
    all_results.append(test_tool_service())
    all_results.append(test_router_service())
    all_results.append(test_async_llm_generation())
    all_results.append(test_tool_parameter())
    
    # Summary
    total_passed = sum(r.passed for r in all_results)
    total_failed = sum(r.failed for r in all_results)
    total = total_passed + total_failed
    
    print("\n" + "="*60)
    print(f"FINAL RESULTS: {total_passed}/{total} tests passed")
    if total_failed > 0:
        print(f"FAILED: {total_failed} tests")
    else:
        print("ALL TESTS PASSED!")
    print("="*60)
    
    return total_failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)