"""Unit tests for deterministic routing."""

import pytest

from agent_core.contracts.agent import Agent, AgentInput, AgentResult
from agent_core.contracts.execution_context import ExecutionContext
from agent_core.runtime.execution_context import create_execution_context
from agent_core.runtime.routing import Router, RoutingError


class MockAgent:
    """Mock agent for testing."""

    def __init__(self, agent_id: str, version: str, capabilities: list[str]):
        """Initialize mock agent."""
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
        return AgentResult(status="success", output={"result": "test"})


class TestRouter:
    """Test Router."""

    def test_select_agent_by_id(self):
        """Test selecting agent by explicit ID."""
        agent1 = MockAgent("agent1", "1.0.0", ["cap1", "cap2"])
        agent2 = MockAgent("agent2", "1.0.0", ["cap3"])

        router = Router({"agent1": agent1, "agent2": agent2})

        selected = router.select_agent(agent_id="agent1")
        assert selected.agent_id == "agent1"

    def test_select_agent_by_capabilities(self):
        """Test selecting agent by required capabilities."""
        agent1 = MockAgent("agent1", "1.0.0", ["cap1", "cap2"])
        agent2 = MockAgent("agent2", "1.0.0", ["cap3"])

        router = Router({"agent1": agent1, "agent2": agent2})

        selected = router.select_agent(required_capabilities=["cap1"])
        assert selected.agent_id == "agent1"

    def test_select_agent_by_capabilities_multiple_match(self):
        """Test that multiple matching agents are resolved deterministically."""
        agent1 = MockAgent("agent_a", "1.0.0", ["cap1", "cap2"])
        agent2 = MockAgent("agent_b", "1.0.0", ["cap1", "cap3"])

        router = Router({"agent_b": agent2, "agent_a": agent1})

        # Should select deterministically (alphabetical by agent_id)
        selected = router.select_agent(required_capabilities=["cap1"])
        assert selected.agent_id == "agent_a"  # Alphabetically first

    def test_select_agent_no_criteria_raises_error(self):
        """Test that selection without criteria raises error."""
        agent1 = MockAgent("agent1", "1.0.0", ["cap1"])
        router = Router({"agent1": agent1})

        with pytest.raises(RoutingError, match="No implicit routing is allowed"):
            router.select_agent()

    def test_select_agent_not_found_raises_error(self):
        """Test that selecting non-existent agent raises error."""
        agent1 = MockAgent("agent1", "1.0.0", ["cap1"])
        router = Router({"agent1": agent1})

        with pytest.raises(RoutingError, match="is not registered"):
            router.select_agent(agent_id="nonexistent")

    def test_select_agent_no_capability_match_raises_error(self):
        """Test that no capability match raises error."""
        agent1 = MockAgent("agent1", "1.0.0", ["cap1"])
        router = Router({"agent1": agent1})

        with pytest.raises(RoutingError, match="No agent found with required capabilities"):
            router.select_agent(required_capabilities=["cap2"])

    def test_list_agents(self):
        """Test listing all registered agents."""
        agent1 = MockAgent("agent1", "1.0.0", ["cap1"])
        agent2 = MockAgent("agent2", "1.0.0", ["cap2"])

        router = Router({"agent1": agent1, "agent2": agent2})

        agent_ids = router.list_agents()
        assert set(agent_ids) == {"agent1", "agent2"}

    def test_get_agent(self):
        """Test getting agent by ID."""
        agent1 = MockAgent("agent1", "1.0.0", ["cap1"])
        router = Router({"agent1": agent1})

        assert router.get_agent("agent1") == agent1
        assert router.get_agent("nonexistent") is None

    def test_capability_matching_requires_all(self):
        """Test that capability matching requires all capabilities."""
        agent1 = MockAgent("agent1", "1.0.0", ["cap1", "cap2"])
        agent2 = MockAgent("agent2", "1.0.0", ["cap1"])

        router = Router({"agent1": agent1, "agent2": agent2})

        # Should match agent1 which has both capabilities
        selected = router.select_agent(required_capabilities=["cap1", "cap2"])
        assert selected.agent_id == "agent1"

        # Should not match agent2 which only has cap1
        with pytest.raises(RoutingError):
            router.select_agent(required_capabilities=["cap1", "cap2", "cap3"])

