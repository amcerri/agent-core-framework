"""Unit tests for main Runtime class."""

import pytest

from agent_core.configuration.schemas import AgentCoreConfig, RuntimeConfig
from agent_core.contracts.agent import Agent, AgentInput, AgentResult
from agent_core.contracts.execution_context import ExecutionContext
from agent_core.runtime.execution_context import create_execution_context
from agent_core.runtime.routing import RoutingError
from agent_core.runtime.runtime import Runtime
from tests.unit.runtime.test_routing import MockAgent


class TestRuntime:
    """Test Runtime class."""

    def test_runtime_initialization(self):
        """Test runtime initialization."""
        config = AgentCoreConfig(
            runtime=RuntimeConfig(runtime_id="test-runtime"),
        )

        runtime = Runtime(config)

        assert runtime.config == config
        assert len(runtime.agents) == 0

    def test_runtime_initialization_requires_runtime_config(self):
        """Test that runtime requires runtime configuration."""
        config = AgentCoreConfig()

        with pytest.raises(ValueError, match="Runtime configuration is required"):
            Runtime(config)

    def test_register_agent(self):
        """Test registering an agent."""
        config = AgentCoreConfig(
            runtime=RuntimeConfig(runtime_id="test-runtime"),
        )
        runtime = Runtime(config)

        agent = MockAgent("agent1", "1.0.0", ["cap1"])
        runtime.register_agent(agent)

        assert "agent1" in runtime.agents
        assert runtime.agents["agent1"] == agent

    def test_execute_agent_by_id(self):
        """Test executing an agent by ID."""
        config = AgentCoreConfig(
            runtime=RuntimeConfig(runtime_id="test-runtime"),
        )
        runtime = Runtime(config)

        agent = MockAgent("agent1", "1.0.0", ["cap1"])
        runtime.register_agent(agent)

        result = runtime.execute_agent(
            agent_id="agent1",
            input_data={"test": "data"},
            initiator="user:test",
        )

        assert result.status == "success"
        assert result.output == {"result": "test"}

    def test_execute_agent_by_capabilities(self):
        """Test executing an agent by capabilities."""
        config = AgentCoreConfig(
            runtime=RuntimeConfig(runtime_id="test-runtime"),
        )
        runtime = Runtime(config)

        agent = MockAgent("agent1", "1.0.0", ["cap1", "cap2"])
        runtime.register_agent(agent)

        result = runtime.execute_agent(
            required_capabilities=["cap1"],
            input_data={"test": "data"},
        )

        assert result.status == "success"

    def test_execute_agent_creates_context_if_not_provided(self):
        """Test that runtime creates context if not provided."""
        config = AgentCoreConfig(
            runtime=RuntimeConfig(runtime_id="test-runtime", default_locale="fr-FR"),
        )
        runtime = Runtime(config)

        agent = MockAgent("agent1", "1.0.0", ["cap1"])

        def check_context(input_data: AgentInput, context: ExecutionContext) -> AgentResult:
            """Agent that checks context."""
            assert context.locale == "fr-FR"  # From runtime config
            assert context.initiator == "user:test"
            return AgentResult(status="success", output={})

        agent.run = check_context
        runtime.register_agent(agent)

        runtime.execute_agent(agent_id="agent1", initiator="user:test")

    def test_execute_agent_with_provided_context(self):
        """Test executing with provided context."""
        config = AgentCoreConfig(
            runtime=RuntimeConfig(runtime_id="test-runtime"),
        )
        runtime = Runtime(config)

        context = create_execution_context(
            initiator="user:custom",
            locale="de-DE",
        )

        agent = MockAgent("agent1", "1.0.0", ["cap1"])

        def check_context(input_data: AgentInput, ctx: ExecutionContext) -> AgentResult:
            """Agent that checks context."""
            assert ctx.locale == "de-DE"  # From provided context
            assert ctx.initiator == "user:custom"
            return AgentResult(status="success", output={})

        agent.run = check_context
        runtime.register_agent(agent)

        runtime.execute_agent(agent_id="agent1", context=context)

    def test_execute_agent_routing_error(self):
        """Test that routing errors are raised."""
        config = AgentCoreConfig(
            runtime=RuntimeConfig(runtime_id="test-runtime"),
        )
        runtime = Runtime(config)

        with pytest.raises(RoutingError):
            runtime.execute_agent(agent_id="nonexistent")

    def test_execute_agent_no_selection_criteria(self):
        """Test that execution without selection criteria fails."""
        config = AgentCoreConfig(
            runtime=RuntimeConfig(runtime_id="test-runtime"),
        )
        runtime = Runtime(config)

        with pytest.raises(RoutingError, match="No implicit routing is allowed"):
            runtime.execute_agent()

    def test_execute_agent_handles_agent_errors(self):
        """Test that agent errors are handled."""
        config = AgentCoreConfig(
            runtime=RuntimeConfig(runtime_id="test-runtime"),
        )
        runtime = Runtime(config)

        agent = MockAgent("agent1", "1.0.0", ["cap1"])

        def failing_agent(input_data: AgentInput, context: ExecutionContext) -> AgentResult:
            """Agent that raises an error."""
            raise ValueError("Agent error")

        agent.run = failing_agent
        runtime.register_agent(agent)

        with pytest.raises(RuntimeError, match="Runtime execution failed"):
            runtime.execute_agent(agent_id="agent1")

    def test_execute_agent_synchronous(self):
        """Test that execution is synchronous (v1 constraint)."""
        config = AgentCoreConfig(
            runtime=RuntimeConfig(runtime_id="test-runtime"),
        )
        runtime = Runtime(config)

        agent = MockAgent("agent1", "1.0.0", ["cap1"])
        runtime.register_agent(agent)

        # Execution should complete immediately (synchronous)
        result = runtime.execute_agent(agent_id="agent1")
        assert result.status == "success"

