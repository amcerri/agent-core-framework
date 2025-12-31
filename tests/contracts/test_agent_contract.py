"""Contract tests for Agent interface and schemas."""

import pytest
from pydantic import ValidationError

from agent_core.contracts.agent import Agent, AgentInput, AgentResult
from agent_core.contracts.execution_context import ExecutionContext
from agent_core.utils.ids import generate_correlation_id, generate_run_id


class TestAgentInputSchema:
    """Test AgentInput schema validation."""

    def test_agent_input_creation_with_payload(self):
        """Test that AgentInput can be created with payload."""
        input_data = AgentInput(payload={"query": "test"})

        assert input_data.payload == {"query": "test"}
        assert input_data.history is None

    def test_agent_input_creation_with_history(self):
        """Test that AgentInput can be created with history."""
        input_data = AgentInput(
            payload={"query": "test"},
            history=[{"role": "user", "content": "previous"}],
        )

        assert input_data.payload == {"query": "test"}
        assert input_data.history == [{"role": "user", "content": "previous"}]

    def test_agent_input_requires_payload(self):
        """Test that AgentInput requires payload field."""
        with pytest.raises(ValidationError):
            AgentInput()


class TestAgentResultSchema:
    """Test AgentResult schema validation."""

    def test_agent_result_creation_with_required_fields(self):
        """Test that AgentResult can be created with required fields."""
        result = AgentResult(
            status="success",
            output={"response": "test"},
        )

        assert result.status == "success"
        assert result.output == {"response": "test"}
        assert result.actions == []
        assert result.errors == []
        assert result.metrics == {}

    def test_agent_result_creation_with_all_fields(self):
        """Test that AgentResult can be created with all fields."""
        result = AgentResult(
            status="success",
            output={"response": "test"},
            actions=[{"type": "tool_call", "tool_id": "test_tool"}],
            errors=[],
            metrics={"latency_ms": 100},
        )

        assert result.status == "success"
        assert result.output == {"response": "test"}
        assert len(result.actions) == 1
        assert result.metrics == {"latency_ms": 100}

    def test_agent_result_requires_status_and_output(self):
        """Test that AgentResult requires status and output."""
        with pytest.raises(ValidationError):
            AgentResult(status="success")

        with pytest.raises(ValidationError):
            AgentResult(output={"test": "data"})


class TestAgentProtocol:
    """Test Agent protocol interface."""

    def test_agent_protocol_can_be_implemented(self):
        """Test that a class can implement the Agent protocol."""

        class MockAgent:
            @property
            def agent_id(self) -> str:
                return "test_agent"

            @property
            def agent_version(self) -> str:
                return "1.0.0"

            @property
            def capabilities(self) -> list[str]:
                return ["test_capability"]

            def run(self, input_data: AgentInput, context: ExecutionContext) -> AgentResult:
                return AgentResult(
                    status="success",
                    output={"result": "test"},
                )

        agent: Agent = MockAgent()

        assert agent.agent_id == "test_agent"
        assert agent.agent_version == "1.0.0"
        assert agent.capabilities == ["test_capability"]

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

        result = agent.run(AgentInput(payload={"test": "data"}), context)
        assert result.status == "success"
        assert result.output == {"result": "test"}
