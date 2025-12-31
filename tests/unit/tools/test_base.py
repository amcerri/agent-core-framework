"""Unit tests for BaseTool."""

import pytest

from agent_core.contracts.execution_context import ExecutionContext
from agent_core.contracts.tool import ToolInput, ToolResult
from agent_core.runtime.execution_context import create_execution_context
from agent_core.tools.base import BaseTool


class ConcreteTool(BaseTool):
    """Concrete tool implementation for testing."""

    def __init__(self, tool_id: str, version: str, permissions: list[str]):
        """Initialize concrete tool."""
        self._tool_id = tool_id
        self._version = version
        self._permissions = permissions

    @property
    def tool_id(self) -> str:
        """Tool identifier."""
        return self._tool_id

    @property
    def tool_version(self) -> str:
        """Tool version."""
        return self._version

    @property
    def permissions_required(self) -> list[str]:
        """Required permissions."""
        return self._permissions

    def execute(self, input_data: ToolInput, context: ExecutionContext) -> ToolResult:
        """Execute tool."""
        return ToolResult(
            status="success",
            output={"result": "test"},
            metrics={"latency_ms": 10.0},
        )


class TestBaseTool:
    """Test BaseTool."""

    def test_base_tool_is_abstract(self):
        """Test that BaseTool cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseTool()  # type: ignore

    def test_concrete_tool_implements_interface(self):
        """Test that concrete tool implements the Tool interface."""
        tool = ConcreteTool("tool1", "1.0.0", ["read", "write"])

        assert tool.tool_id == "tool1"
        assert tool.tool_version == "1.0.0"
        assert tool.permissions_required == ["read", "write"]

    def test_concrete_tool_execute(self):
        """Test that concrete tool can execute."""
        tool = ConcreteTool("tool1", "1.0.0", ["read"])
        context = create_execution_context(initiator="user:test")
        input_data = ToolInput(payload={"test": "data"})

        result = tool.execute(input_data, context)

        assert result.status == "success"
        assert result.output == {"result": "test"}
        assert result.metrics["latency_ms"] == 10.0

    def test_tool_conforms_to_protocol(self):
        """Test that BaseTool subclasses conform to Tool Protocol."""
        tool = ConcreteTool("tool1", "1.0.0", ["read"])

        # Type check: tool should be assignable to Tool Protocol
        tool_protocol: BaseTool = tool
        assert tool_protocol.tool_id == "tool1"
