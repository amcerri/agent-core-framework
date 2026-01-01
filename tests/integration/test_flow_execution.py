"""Integration tests for flow execution."""

import pytest

from agent_core.agents.base import BaseAgent
from agent_core.configuration.schemas import AgentCoreConfig, FlowConfig, RuntimeConfig
from agent_core.contracts.agent import AgentInput, AgentResult
from agent_core.contracts.execution_context import ExecutionContext
from agent_core.orchestration.flow_engine import FlowExecutionError, SimpleFlowEngine
from agent_core.runtime.execution_context import create_execution_context
from agent_core.runtime.runtime import Runtime


class MockAgent(BaseAgent):
    """Mock agent for flow testing."""

    def __init__(self, agent_id: str):
        """Initialize mock agent."""
        self._agent_id = agent_id
        self.execution_count = 0

    @property
    def agent_id(self) -> str:
        """Agent identifier."""
        return self._agent_id

    @property
    def agent_version(self) -> str:
        """Agent version."""
        return "1.0.0"

    @property
    def capabilities(self) -> list[str]:
        """Agent capabilities."""
        return ["test"]

    def run(self, input_data: AgentInput, context: ExecutionContext) -> AgentResult:
        """Execute agent."""
        self.execution_count += 1
        return AgentResult(
            status="success",
            output={"result": f"executed_{self._agent_id}"},
        )


@pytest.fixture
def runtime_config():
    """Create runtime configuration."""
    return AgentCoreConfig(runtime=RuntimeConfig(runtime_id="test_runtime"))


@pytest.fixture
def mock_runtime(runtime_config):
    """Create mock runtime with agents."""
    agent1 = MockAgent("agent1")
    agent2 = MockAgent("agent2")

    runtime = Runtime(
        config=runtime_config,
        agents={"agent1": agent1, "agent2": agent2},
    )

    return runtime


@pytest.fixture
def simple_flow_config():
    """Create a simple flow configuration."""
    return FlowConfig(
        flow_id="test_flow",
        version="1.0.0",
        entrypoint="start",
        nodes={
            "start": {"type": "agent", "agent_id": "agent1"},
            "end": {"type": "agent", "agent_id": "agent2"},
        },
        transitions=[
            {"from": "start", "to": "end"},
        ],
    )


class TestFlowExecution:
    """Integration tests for flow execution."""

    def test_execute_simple_flow(self, mock_runtime, simple_flow_config):
        """Test executing a simple flow."""
        context = create_execution_context(initiator="user:test")

        engine = SimpleFlowEngine(
            flow=simple_flow_config,
            context=context,
            runtime=mock_runtime,
        )

        result = engine.execute()

        assert result["status"] == "completed"
        assert result["flow_id"] == "test_flow"
        assert result["final_node"] == "end"

        # Verify agents were executed
        assert mock_runtime.agents["agent1"].execution_count == 1
        assert mock_runtime.agents["agent2"].execution_count == 1

    def test_execute_flow_with_condition(self, mock_runtime):
        """Test executing a flow with conditional transition."""
        flow_config = FlowConfig(
            flow_id="conditional_flow",
            version="1.0.0",
            entrypoint="start",
            nodes={
                "start": {"type": "agent", "agent_id": "agent1"},
                "branch_a": {"type": "agent", "agent_id": "agent2"},
                "branch_b": {"type": "agent", "agent_id": "agent2"},
            },
            transitions=[
                {
                    "from": "start",
                    "to": "branch_a",
                    "condition": {"status": "success"},
                },
            ],
        )

        context = create_execution_context(initiator="user:test")

        engine = SimpleFlowEngine(
            flow=flow_config,
            context=context,
            runtime=mock_runtime,
        )

        result = engine.execute()

        assert result["status"] == "completed"
        # Should have executed start and branch_a
        assert mock_runtime.agents["agent1"].execution_count == 1
        assert mock_runtime.agents["agent2"].execution_count == 1

    def test_execute_flow_invalid_node(self, mock_runtime):
        """Test executing a flow with invalid node reference."""
        flow_config = FlowConfig(
            flow_id="invalid_flow",
            version="1.0.0",
            entrypoint="start",
            nodes={
                "start": {"type": "agent", "agent_id": "agent1"},
            },
            transitions=[
                {"from": "start", "to": "nonexistent"},
            ],
        )

        context = create_execution_context(initiator="user:test")

        engine = SimpleFlowEngine(
            flow=flow_config,
            context=context,
            runtime=mock_runtime,
        )

        with pytest.raises(FlowExecutionError, match="not found"):
            engine.execute()

    def test_flow_state_tracking(self, mock_runtime, simple_flow_config):
        """Test that flow state is tracked correctly."""
        context = create_execution_context(initiator="user:test")

        engine = SimpleFlowEngine(
            flow=simple_flow_config,
            context=context,
            runtime=mock_runtime,
        )

        engine.execute()

        state = engine.get_state()

        assert state.current_node == "end"
        assert len(state.history) > 0
        assert any("start" in str(h) for h in state.history)
