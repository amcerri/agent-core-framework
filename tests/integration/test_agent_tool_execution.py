"""Integration tests for agent → runtime → tool execution."""

import pytest

from agent_core.agents.base import BaseAgent
from agent_core.configuration.schemas import AgentCoreConfig, RuntimeConfig
from agent_core.contracts.agent import AgentInput, AgentResult
from agent_core.contracts.execution_context import ExecutionContext
from agent_core.contracts.tool import ToolInput, ToolResult
from agent_core.runtime.execution_context import create_execution_context
from agent_core.runtime.runtime import Runtime
from agent_core.tools.base import BaseTool


class MockAgent(BaseAgent):
    """Mock agent that requests tool execution."""

    def __init__(self, agent_id: str = "test_agent"):
        """Initialize mock agent."""
        self._agent_id = agent_id

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
        """Execute agent and request tool execution."""
        # Request tool execution via actions
        actions = [{"type": "tool", "tool_id": "test_tool", "payload": {"input": "test"}}]
        return AgentResult(
            status="success",
            output={"message": "agent completed"},
            actions=actions,
        )


class MockTool(BaseTool):
    """Mock tool for integration testing."""

    def __init__(self, tool_id: str = "test_tool"):
        """Initialize mock tool."""
        self._tool_id = tool_id
        self.execution_count = 0

    @property
    def tool_id(self) -> str:
        """Tool identifier."""
        return self._tool_id

    @property
    def tool_version(self) -> str:
        """Tool version."""
        return "1.0.0"

    @property
    def permissions_required(self) -> list[str]:
        """Required permissions."""
        return ["read"]

    def execute(self, input_data: ToolInput, context: ExecutionContext) -> ToolResult:
        """Execute tool."""
        self.execution_count += 1
        return ToolResult(
            status="success",
            output={"result": f"processed_{input_data.payload.get('input', '')}"},
            metrics={"latency_ms": 5.0},
        )


@pytest.fixture
def runtime_config():
    """Create runtime configuration."""
    return AgentCoreConfig(runtime=RuntimeConfig(runtime_id="test_runtime"))


@pytest.fixture
def test_agent():
    """Create test agent."""
    return MockAgent()


@pytest.fixture
def test_tool():
    """Create test tool."""
    return MockTool()


class TestAgentToolExecution:
    """Integration tests for agent → runtime → tool execution."""

    def test_agent_execution_triggers_tool_execution(self, runtime_config, test_agent, test_tool):
        """Test that agent execution triggers tool execution through runtime."""
        # Create runtime with agent and tool
        runtime = Runtime(
            config=runtime_config,
            agents={"test_agent": test_agent},
            tools={"test_tool": test_tool},
        )

        # Execute agent
        context = create_execution_context(
            initiator="user:test",
            permissions={"read": True},
        )
        result = runtime.execute_agent(
            agent_id="test_agent",
            input_data={"test": "data"},
            context=context,
        )

        # Verify agent result
        assert result.status == "success"
        assert result.output["message"] == "agent completed"

        # Verify tool was executed
        assert test_tool.execution_count == 1

    def test_agent_cannot_call_tool_directly(self, test_agent, test_tool):
        """Test that agents cannot call tools directly (must go through runtime)."""
        # This test verifies the architectural boundary:
        # Agents return actions, runtime executes them
        context = create_execution_context(
            initiator="user:test",
            permissions={"read": True},
        )

        # Agent runs and returns actions
        agent_input = AgentInput(payload={"test": "data"})
        result = test_agent.run(agent_input, context)

        # Agent should return actions, not execute tool directly
        assert len(result.actions) == 1
        assert result.actions[0]["type"] == "tool"
        assert result.actions[0]["tool_id"] == "test_tool"

        # Tool should not have been executed yet (no direct call)
        assert test_tool.execution_count == 0

    def test_runtime_enforces_governance_before_tool_execution(
        self, runtime_config, test_agent, test_tool
    ):
        """Test that runtime enforces governance before tool execution."""
        # Create runtime
        runtime = Runtime(
            config=runtime_config,
            agents={"test_agent": test_agent},
            tools={"test_tool": test_tool},
        )

        # Execute agent with insufficient permissions
        context = create_execution_context(
            initiator="user:test",
            permissions={"write": True},  # Missing "read" permission
        )

        result = runtime.execute_agent(
            agent_id="test_agent",
            input_data={},
            context=context,
        )

        # Tool should not have been executed due to permission check
        assert test_tool.execution_count == 0

        # Result should contain error
        assert len(result.errors) > 0
        assert any("Permission denied" in str(error.get("error", "")) for error in result.errors)
