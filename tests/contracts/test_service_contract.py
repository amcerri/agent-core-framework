"""Contract tests for Service interface."""

from agent_core.contracts.execution_context import ExecutionContext
from agent_core.contracts.service import Service, ServiceInput, ServiceResult
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

            def execute(
                self, input_data: ServiceInput, context: ExecutionContext
            ) -> ServiceResult:
                return ServiceResult(
                    status="success",
                    output={"action": input_data.action, "payload": input_data.payload},
                    errors=[],
                    metrics={},
                )

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

        # Test execute method
        service_input = ServiceInput(action="read", payload={"key": "test"})
        result = service.execute(service_input, context)
        assert isinstance(result, ServiceResult)
        assert result.status == "success"
        assert result.output["action"] == "read"
        assert result.output["payload"] == {"key": "test"}
        assert result.errors == []
        assert result.metrics == {}

    def test_service_input_schema(self):
        """Test ServiceInput schema validation."""
        # Valid input
        service_input = ServiceInput(action="read", payload={"key": "value"})
        assert service_input.action == "read"
        assert service_input.payload == {"key": "value"}

        # Action is required
        try:
            ServiceInput(payload={"key": "value"})  # type: ignore
            assert False, "Should raise validation error"
        except Exception:
            pass

        # Payload is required
        try:
            ServiceInput(action="read")  # type: ignore
            assert False, "Should raise validation error"
        except Exception:
            pass

    def test_service_result_schema(self):
        """Test ServiceResult schema validation."""
        # Valid result with defaults
        result = ServiceResult(status="success", output={})
        assert result.status == "success"
        assert result.output == {}
        assert result.errors == []
        assert result.metrics == {}

        # Result with all fields
        result = ServiceResult(
            status="error",
            output={"error": "test"},
            errors=[{"error": "test_error"}],
            metrics={"latency_ms": 10.0},
        )
        assert result.status == "error"
        assert result.output == {"error": "test"}
        assert len(result.errors) == 1
        assert result.metrics["latency_ms"] == 10.0

        # Status is required
        try:
            ServiceResult(output={})  # type: ignore
            assert False, "Should raise validation error"
        except Exception:
            pass

        # Output is required
        try:
            ServiceResult(status="success")  # type: ignore
            assert False, "Should raise validation error"
        except Exception:
            pass
