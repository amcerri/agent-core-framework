"""Contract tests for Service interface."""

from agent_core.contracts.execution_context import ExecutionContext
from agent_core.contracts.service import Service
from agent_core.utils.ids import generate_correlation_id, generate_run_id


class TestServiceProtocol:
    """Test Service protocol interface."""

    def test_service_protocol_can_be_implemented(self):
        """Test that a class can implement the Service protocol."""

        class MockService:
            @property
            def service_id(self) -> str:
                return "test_service"

            @property
            def service_version(self) -> str:
                return "1.0.0"

            @property
            def capabilities(self) -> list[str]:
                return ["read", "write"]

            def check_permission(self, action: str, context: ExecutionContext) -> bool:
                return action in context.permissions

        service: Service = MockService()

        assert service.service_id == "test_service"
        assert service.service_version == "1.0.0"
        assert service.capabilities == ["read", "write"]

        run_id = generate_run_id()
        correlation_id = generate_correlation_id()
        context = ExecutionContext(
            run_id=run_id,
            correlation_id=correlation_id,
            initiator="user:test",
            permissions={"read": True},
            budget={},
            locale="en-US",
            observability={},
        )

        assert service.check_permission("read", context) is True
        assert service.check_permission("write", context) is False
