"""Contract tests for Tool interface and schemas."""

import pytest
from pydantic import ValidationError

from agent_core.contracts.execution_context import ExecutionContext
from agent_core.contracts.tool import Tool, ToolInput, ToolResult
from agent_core.utils.ids import generate_correlation_id, generate_run_id


class TestToolInputSchema:
    """Test ToolInput schema validation."""

    def test_tool_input_creation_with_payload(self):
        """Test that ToolInput can be created with payload."""
        input_data = ToolInput(payload={"command": "test"})

        assert input_data.payload == {"command": "test"}
        assert input_data.timeout is None
        assert input_data.retry_policy is None

    def test_tool_input_creation_with_timeout(self):
        """Test that ToolInput can be created with timeout."""
        input_data = ToolInput(payload={"command": "test"}, timeout=30.0)

        assert input_data.payload == {"command": "test"}
        assert input_data.timeout == 30.0

    def test_tool_input_creation_with_retry_policy(self):
        """Test that ToolInput can be created with retry policy."""
        input_data = ToolInput(
            payload={"command": "test"},
            retry_policy={"max_retries": 3, "backoff": "exponential"},
        )

        assert input_data.payload == {"command": "test"}
        assert input_data.retry_policy == {
            "max_retries": 3,
            "backoff": "exponential",
        }

    def test_tool_input_requires_payload(self):
        """Test that ToolInput requires payload field."""
        with pytest.raises(ValidationError):
            ToolInput()


class TestToolResultSchema:
    """Test ToolResult schema validation."""

    def test_tool_result_creation_with_required_fields(self):
        """Test that ToolResult can be created with required fields."""
        result = ToolResult(
            status="success",
            output={"result": "test"},
        )

        assert result.status == "success"
        assert result.output == {"result": "test"}
        assert result.errors == []
        assert result.metrics == {}

    def test_tool_result_creation_with_all_fields(self):
        """Test that ToolResult can be created with all fields."""
        result = ToolResult(
            status="success",
            output={"result": "test"},
            errors=[],
            metrics={"latency_ms": 50},
        )

        assert result.status == "success"
        assert result.output == {"result": "test"}
        assert result.metrics == {"latency_ms": 50}

    def test_tool_result_requires_status_and_output(self):
        """Test that ToolResult requires status and output."""
        with pytest.raises(ValidationError):
            ToolResult(status="success")

        with pytest.raises(ValidationError):
            ToolResult(output={"test": "data"})


class TestToolProtocol:
    """Test Tool protocol interface."""

    def test_tool_protocol_can_be_implemented(self):
        """Test that a class can implement the Tool protocol."""

        class MockTool:
            @property
            def tool_id(self) -> str:
                return "test_tool"

            @property
            def tool_version(self) -> str:
                return "1.0.0"

            @property
            def permissions_required(self) -> list[str]:
                return ["read", "write"]

            def execute(self, input_data: ToolInput, context: ExecutionContext) -> ToolResult:
                return ToolResult(
                    status="success",
                    output={"result": "executed"},
                )

        tool: Tool = MockTool()

        assert tool.tool_id == "test_tool"
        assert tool.tool_version == "1.0.0"
        assert tool.permissions_required == ["read", "write"]

        run_id = generate_run_id()
        correlation_id = generate_correlation_id()
        context = ExecutionContext(
            run_id=run_id,
            correlation_id=correlation_id,
            initiator="user:test",
            permissions={},
            budget={},
            locale="en-US",
            observability={},
        )

        result = tool.execute(ToolInput(payload={"test": "data"}), context)
        assert result.status == "success"
        assert result.output == {"result": "executed"}
