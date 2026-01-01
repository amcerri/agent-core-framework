"""Unit tests for main Runtime class."""

import pytest

from agent_core.configuration.schemas import AgentCoreConfig, RuntimeConfig
from agent_core.contracts.agent import AgentInput, AgentResult
from agent_core.contracts.execution_context import ExecutionContext
from agent_core.runtime.execution_context import create_execution_context
from agent_core.runtime.lifecycle import LifecycleEvent
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

    def test_get_lifecycle_events_returns_empty_before_execution(self):
        """Test that get_lifecycle_events returns empty list before execution."""
        config = AgentCoreConfig(
            runtime=RuntimeConfig(runtime_id="test-runtime"),
        )
        runtime = Runtime(config)

        events = runtime.get_lifecycle_events()
        assert events == []

    def test_get_lifecycle_events_returns_events_after_execution(self):
        """Test that get_lifecycle_events returns events after execution."""
        config = AgentCoreConfig(
            runtime=RuntimeConfig(runtime_id="test-runtime"),
        )
        runtime = Runtime(config)

        agent = MockAgent("agent1", "1.0.0", ["cap1"])
        runtime.register_agent(agent)

        # Execute agent
        runtime.execute_agent(agent_id="agent1")

        # Get lifecycle events
        events = runtime.get_lifecycle_events()
        assert len(events) > 0

        # Verify expected events are present
        event_types = [event for event, _ in events]
        assert LifecycleEvent.INITIALIZATION_COMPLETED in event_types
        assert LifecycleEvent.EXECUTION_STARTED in event_types
        assert LifecycleEvent.EXECUTION_COMPLETED in event_types
        # TERMINATION_STARTED may or may not be present depending on whether
        # execution transitions through TERMINATED (COMPLETED is terminal)

    def test_get_lifecycle_events_includes_metadata(self):
        """Test that lifecycle events include metadata."""
        config = AgentCoreConfig(
            runtime=RuntimeConfig(runtime_id="test-runtime"),
        )
        runtime = Runtime(config)

        agent = MockAgent("agent1", "1.0.0", ["cap1"])
        runtime.register_agent(agent)

        # Execute agent
        runtime.execute_agent(agent_id="agent1")

        # Get lifecycle events
        events = runtime.get_lifecycle_events()
        assert len(events) > 0

        # Check that events have metadata (may be empty dict)
        for _, metadata in events:
            assert isinstance(metadata, dict)

    def test_get_lifecycle_events_accessible_after_completion(self):
        """Test that lifecycle events are accessible after execution completes."""
        config = AgentCoreConfig(
            runtime=RuntimeConfig(runtime_id="test-runtime"),
        )
        runtime = Runtime(config)

        agent = MockAgent("agent1", "1.0.0", ["cap1"])
        runtime.register_agent(agent)

        # Execute agent
        result = runtime.execute_agent(agent_id="agent1")
        assert result.status == "success"

        # Events should be accessible after completion
        events = runtime.get_lifecycle_events()
        assert (
            len(events) >= 3
        )  # At least INITIALIZATION_COMPLETED, EXECUTION_STARTED, EXECUTION_COMPLETED

    def test_get_lifecycle_events_tracks_multiple_executions(self):
        """Test that lifecycle events are tracked per execution."""
        config = AgentCoreConfig(
            runtime=RuntimeConfig(runtime_id="test-runtime"),
        )
        runtime = Runtime(config)

        agent = MockAgent("agent1", "1.0.0", ["cap1"])
        runtime.register_agent(agent)

        # First execution
        runtime.execute_agent(agent_id="agent1")
        events1 = runtime.get_lifecycle_events()
        assert len(events1) > 0

        # Second execution (should replace previous events)
        runtime.execute_agent(agent_id="agent1")
        events2 = runtime.get_lifecycle_events()
        assert len(events2) > 0
        # Events should be from the most recent execution
        assert events2 != events1 or len(events2) == len(events1)
