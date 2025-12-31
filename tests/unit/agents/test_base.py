"""Unit tests for BaseAgent."""

import pytest

from agent_core.agents.base import BaseAgent
from agent_core.contracts.agent import AgentInput, AgentResult
from agent_core.contracts.execution_context import ExecutionContext
from agent_core.runtime.execution_context import create_execution_context


class ConcreteAgent(BaseAgent):
    """Concrete agent implementation for testing."""

    def __init__(self, agent_id: str, version: str, capabilities: list[str]):
        """Initialize concrete agent."""
        self._agent_id = agent_id
        self._version = version
        self._capabilities = capabilities

    @property
    def agent_id(self) -> str:
        """Agent identifier."""
        return self._agent_id

    @property
    def agent_version(self) -> str:
        """Agent version."""
        return self._version

    @property
    def capabilities(self) -> list[str]:
        """Agent capabilities."""
        return self._capabilities

    def run(self, input_data: AgentInput, context: ExecutionContext) -> AgentResult:
        """Execute agent."""
        return AgentResult(
            status="success",
            output={"result": "test"},
            actions=[{"type": "tool", "tool_id": "test_tool"}],
        )


class TestBaseAgent:
    """Test BaseAgent."""

    def test_base_agent_is_abstract(self):
        """Test that BaseAgent cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseAgent()  # type: ignore

    def test_concrete_agent_implements_interface(self):
        """Test that concrete agent implements the Agent interface."""
        agent = ConcreteAgent("agent1", "1.0.0", ["cap1", "cap2"])

        assert agent.agent_id == "agent1"
        assert agent.agent_version == "1.0.0"
        assert agent.capabilities == ["cap1", "cap2"]

    def test_concrete_agent_run(self):
        """Test that concrete agent can execute."""
        agent = ConcreteAgent("agent1", "1.0.0", ["cap1"])
        context = create_execution_context(initiator="user:test")
        input_data = AgentInput(payload={"test": "data"})

        result = agent.run(input_data, context)

        assert result.status == "success"
        assert result.output == {"result": "test"}
        assert len(result.actions) == 1

    def test_agent_conforms_to_protocol(self):
        """Test that BaseAgent subclasses conform to Agent Protocol."""
        agent = ConcreteAgent("agent1", "1.0.0", ["cap1"])

        # Type check: agent should be assignable to Agent Protocol
        agent_protocol: BaseAgent = agent
        assert agent_protocol.agent_id == "agent1"
