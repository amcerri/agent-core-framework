"""Integration tests for service execution via runtime."""

from typing import Any

from agent_core.contracts.execution_context import ExecutionContext
from agent_core.contracts.service import ServiceInput, ServiceResult
from agent_core.runtime.execution_context import create_execution_context
from agent_core.runtime.runtime import Runtime
from agent_core.services.base import BaseService


class MockStorageService(BaseService):
    """Test storage service for integration tests."""

    def __init__(self):
        """Initialize test storage service."""
        self._storage: dict[str, dict[str, Any]] = {}

    @property
    def service_id(self) -> str:
        """Service identifier."""
        return "test_storage_service"

    @property
    def service_version(self) -> str:
        """Service version."""
        return "1.0.0"

    @property
    def capabilities(self) -> list[str]:
        """Service capabilities."""
        return ["storage", "retrieval"]

    def check_permission(self, action: str, context: ExecutionContext) -> bool:
        """Check if action is permitted."""
        permissions = context.permissions
        if action in ["read", "get"]:
            return permissions.get("read", False) or permissions.get("storage", False)
        elif action in ["write", "set"]:
            return permissions.get("write", False) or permissions.get("storage", False)
        return False

    def execute(
        self, input_data: ServiceInput, context: ExecutionContext
    ) -> ServiceResult:
        """Execute a service action."""
        action = input_data.action
        payload = input_data.payload

        if not self.check_permission(action, context):
            return ServiceResult(
                status="error",
                output={},
                errors=[{"error": "permission_denied"}],
                metrics={},
            )

        if action == "get":
            key = payload.get("key")
            if key is None:
                return ServiceResult(
                    status="error",
                    output={},
                    errors=[{"error": "missing_key"}],
                    metrics={},
                )
            value = self._storage.get(key)
            return ServiceResult(
                status="success",
                output={"key": key, "value": value},
                errors=[],
                metrics={},
            )

        elif action == "set":
            key = payload.get("key")
            value = payload.get("value")
            if key is None or value is None:
                return ServiceResult(
                    status="error",
                    output={},
                    errors=[{"error": "missing_parameters"}],
                    metrics={},
                )
            if not isinstance(value, dict):
                return ServiceResult(
                    status="error",
                    output={},
                    errors=[{"error": "invalid_value"}],
                    metrics={},
                )
            self._storage[key] = value
            return ServiceResult(
                status="success",
                output={"key": key, "stored": True},
                errors=[],
                metrics={},
            )

        else:
            return ServiceResult(
                status="error",
                output={},
                errors=[{"error": "unknown_action"}],
                metrics={},
            )


class TestServiceAgent:
    """Test agent that requests service actions."""

    @property
    def agent_id(self) -> str:
        """Agent identifier."""
        return "test_service_agent"

    @property
    def agent_version(self) -> str:
        """Agent version."""
        return "1.0.0"

    @property
    def capabilities(self) -> list[str]:
        """Agent capabilities."""
        return ["service_access"]

    def run(self, input_data, context: ExecutionContext):
        """Request service actions."""
        from agent_core.contracts.agent import AgentResult

        actions = [
            {
                "type": "service",
                "service_id": "test_storage_service",
                "action": "set",
                "payload": {"key": "test_key", "value": {"data": "test_value"}},
            },
            {
                "type": "service",
                "service_id": "test_storage_service",
                "action": "get",
                "payload": {"key": "test_key"},
            },
        ]
        return AgentResult(
            status="success",
            output={},
            actions=actions,
            errors=[],
            metrics={},
        )


def test_service_execution_via_runtime():
    """Test that services can be executed via runtime actions."""
    from agent_core.configuration.schemas import AgentCoreConfig, RuntimeConfig

    # Create minimal config
    config = AgentCoreConfig(runtime=RuntimeConfig(runtime_id="test_runtime"))

    # Create runtime
    runtime = Runtime(config=config)

    # Register service
    service = MockStorageService()
    runtime.register_service(service)

    # Register agent
    agent = TestServiceAgent()
    runtime.register_agent(agent)

    # Create context with permissions
    context = create_execution_context(
        initiator="user:test",
        permissions={"storage": True, "write": True, "read": True},
        budget={"time_limit": 60, "max_calls": 10},
    )

    # Execute agent which will trigger service actions
    result = runtime.execute_agent(
        agent_id="test_service_agent",
        input_data={},
        context=context,
    )

    # Verify agent execution succeeded
    assert result.status == "success"
    assert len(result.actions) == 2

    # Verify service storage was updated
    assert len(service._storage) == 1
    assert service._storage["test_key"] == {"data": "test_value"}


def test_service_execution_permission_denied():
    """Test that service execution is denied without permissions."""
    from agent_core.configuration.schemas import AgentCoreConfig, RuntimeConfig

    # Create minimal config
    config = AgentCoreConfig(runtime=RuntimeConfig(runtime_id="test_runtime"))

    # Create runtime
    runtime = Runtime(config=config)

    # Register service
    service = MockStorageService()
    runtime.register_service(service)

    # Register agent
    agent = TestServiceAgent()
    runtime.register_agent(agent)

    # Create context without permissions
    context = create_execution_context(
        initiator="user:test",
        permissions={},  # No permissions
        budget={"time_limit": 60, "max_calls": 10},
    )

    # Execute agent which will trigger service actions
    result = runtime.execute_agent(
        agent_id="test_service_agent",
        input_data={},
        context=context,
    )

    # Verify agent execution succeeded (agent itself succeeded)
    # but actions failed (check action_results)
    assert result.status == "success"
    # Actions should have failed, but agent execution itself succeeded
    # The runtime collects action errors but doesn't fail the agent execution
    # Verify service storage was not updated (actions failed)
    assert len(service._storage) == 0


def test_service_execution_direct():
    """Test that services can be executed directly (not via runtime)."""
    service = MockStorageService()

    context = create_execution_context(
        initiator="user:test",
        permissions={"storage": True, "write": True, "read": True},
    )

    # Execute set action
    set_input = ServiceInput(
        action="set", payload={"key": "direct_key", "value": {"data": "direct_value"}}
    )
    set_result = service.execute(set_input, context)
    assert set_result.status == "success"
    assert set_result.output["stored"] is True

    # Execute get action
    get_input = ServiceInput(action="get", payload={"key": "direct_key"})
    get_result = service.execute(get_input, context)
    assert get_result.status == "success"
    assert get_result.output["value"] == {"data": "direct_value"}

    # Verify storage
    assert len(service._storage) == 1
    assert service._storage["direct_key"] == {"data": "direct_value"}

