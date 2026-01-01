"""Edge case tests for service execution."""

from agent_core.configuration.schemas import AgentCoreConfig, RuntimeConfig
from agent_core.contracts.execution_context import ExecutionContext
from agent_core.contracts.service import ServiceInput, ServiceResult
from agent_core.runtime.execution_context import create_execution_context
from agent_core.runtime.runtime import Runtime
from agent_core.services.base import BaseService


class ErrorService(BaseService):
    """Service that returns errors for testing."""

    @property
    def service_id(self) -> str:
        """Service identifier."""
        return "error_service"

    @property
    def service_version(self) -> str:
        """Service version."""
        return "1.0.0"

    @property
    def capabilities(self) -> list[str]:
        """Service capabilities."""
        return ["error_testing"]

    def check_permission(self, action: str, context: ExecutionContext) -> bool:
        """Check if action is permitted."""
        return context.permissions.get("test", False)

    def execute(self, input_data: ServiceInput, context: ExecutionContext) -> ServiceResult:
        """Execute service action with error handling."""
        action = input_data.action

        if action == "error":
            return ServiceResult(
                status="error",
                output={},
                errors=[{"error": "test_error", "code": "TEST_ERROR"}],
                metrics={"attempts": 1},
            )

        if action == "partial_success":
            return ServiceResult(
                status="partial",
                output={"partial": True},
                errors=[{"warning": "partial_result"}],
                metrics={},
            )

        return ServiceResult(
            status="success",
            output={"action": action},
            errors=[],
            metrics={},
        )


def test_service_execution_with_errors():
    """Test service execution that returns error status."""
    config = AgentCoreConfig(runtime=RuntimeConfig(runtime_id="test_runtime"))
    runtime = Runtime(config=config)

    service = ErrorService()
    runtime.register_service(service)

    context = create_execution_context(
        initiator="user:test",
        permissions={"test": True},
        budget={"time_limit": 60, "max_calls": 10},
    )

    # Execute action that returns error
    action = {
        "type": "service",
        "service_id": "error_service",
        "action": "error",
        "payload": {},
    }

    result = runtime.execute_action(action, context)

    # Verify error result is returned
    assert result["status"] == "error"
    assert len(result.get("errors", [])) > 0
    assert "test_error" in str(result.get("errors", []))


def test_service_execution_with_partial_status():
    """Test service execution that returns partial success status."""
    config = AgentCoreConfig(runtime=RuntimeConfig(runtime_id="test_runtime"))
    runtime = Runtime(config=config)

    service = ErrorService()
    runtime.register_service(service)

    context = create_execution_context(
        initiator="user:test",
        permissions={"test": True},
        budget={"time_limit": 60, "max_calls": 10},
    )

    # Execute action that returns partial success
    action = {
        "type": "service",
        "service_id": "error_service",
        "action": "partial_success",
        "payload": {},
    }

    result = runtime.execute_action(action, context)

    # Verify partial result is returned
    assert result["status"] == "partial"
    assert result.get("output", {}).get("partial") is True
    assert len(result.get("errors", [])) > 0


def test_service_execution_with_metrics():
    """Test service execution that includes metrics."""
    config = AgentCoreConfig(runtime=RuntimeConfig(runtime_id="test_runtime"))
    runtime = Runtime(config=config)

    service = ErrorService()
    runtime.register_service(service)

    context = create_execution_context(
        initiator="user:test",
        permissions={"test": True},
        budget={"time_limit": 60, "max_calls": 10},
    )

    # Execute action that returns metrics
    action = {
        "type": "service",
        "service_id": "error_service",
        "action": "error",
        "payload": {},
    }

    result = runtime.execute_action(action, context)

    # Verify metrics are included
    assert "metrics" in result
    assert result["metrics"].get("attempts") == 1
