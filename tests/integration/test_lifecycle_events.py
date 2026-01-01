"""Integration tests for lifecycle event tracking."""

from agent_core.configuration.schemas import AgentCoreConfig, RuntimeConfig
from agent_core.contracts.agent import AgentInput, AgentResult
from agent_core.contracts.execution_context import ExecutionContext
from agent_core.runtime.execution_context import create_execution_context
from agent_core.runtime.lifecycle import LifecycleEvent
from agent_core.runtime.runtime import Runtime


class TestAgent:
    """Test agent for lifecycle event tests."""

    @property
    def agent_id(self) -> str:
        """Agent identifier."""
        return "test_agent"

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
        return AgentResult(
            status="success",
            output={"result": "test"},
            actions=[],
            errors=[],
            metrics={},
        )


def test_lifecycle_events_tracked_during_execution():
    """Test that lifecycle events are tracked during execution."""
    config = AgentCoreConfig(runtime=RuntimeConfig(runtime_id="test_runtime"))
    runtime = Runtime(config=config)

    agent = TestAgent()
    runtime.register_agent(agent)

    # Execute agent
    context = create_execution_context(
        initiator="user:test",
        permissions={},
        budget={"time_limit": 60, "max_calls": 10},
    )
    result = runtime.execute_agent(agent_id="test_agent", context=context)

    # Verify execution succeeded
    assert result.status == "success"

    # Get lifecycle events
    events = runtime.get_lifecycle_events()
    assert len(events) > 0

    # Verify expected events are present
    event_types = [event for event, _ in events]
    assert LifecycleEvent.INITIALIZATION_COMPLETED in event_types
    assert LifecycleEvent.EXECUTION_STARTED in event_types
    assert LifecycleEvent.EXECUTION_COMPLETED in event_types


def test_lifecycle_events_accessible_after_completion():
    """Test that lifecycle events are accessible after execution completes."""
    config = AgentCoreConfig(runtime=RuntimeConfig(runtime_id="test_runtime"))
    runtime = Runtime(config=config)

    agent = TestAgent()
    runtime.register_agent(agent)

    # Execute agent
    context = create_execution_context(
        initiator="user:test",
        permissions={},
        budget={"time_limit": 60, "max_calls": 10},
    )
    result = runtime.execute_agent(agent_id="test_agent", context=context)
    assert result.status == "success"

    # Events should be accessible after completion
    events = runtime.get_lifecycle_events()
    assert (
        len(events) >= 3
    )  # At least INITIALIZATION_COMPLETED, EXECUTION_STARTED, EXECUTION_COMPLETED

    # Verify events are in correct order
    event_types = [event for event, _ in events]
    assert event_types[0] == LifecycleEvent.INITIALIZATION_COMPLETED
    assert event_types[1] == LifecycleEvent.EXECUTION_STARTED
    assert event_types[2] == LifecycleEvent.EXECUTION_COMPLETED


def test_lifecycle_events_include_metadata():
    """Test that lifecycle events include metadata from transitions."""
    config = AgentCoreConfig(runtime=RuntimeConfig(runtime_id="test_runtime"))
    runtime = Runtime(config=config)

    agent = TestAgent()
    runtime.register_agent(agent)

    # Execute agent
    context = create_execution_context(
        initiator="user:test",
        permissions={},
        budget={"time_limit": 60, "max_calls": 10},
    )
    runtime.execute_agent(agent_id="test_agent", context=context)

    # Get lifecycle events
    events = runtime.get_lifecycle_events()
    assert len(events) > 0

    # Verify all events have metadata (may be empty dict)
    for _, metadata in events:
        assert isinstance(metadata, dict)


def test_lifecycle_events_tracked_per_execution():
    """Test that lifecycle events are tracked per execution."""
    config = AgentCoreConfig(runtime=RuntimeConfig(runtime_id="test_runtime"))
    runtime = Runtime(config=config)

    agent = TestAgent()
    runtime.register_agent(agent)

    context = create_execution_context(
        initiator="user:test",
        permissions={},
        budget={"time_limit": 60, "max_calls": 10},
    )

    # First execution
    runtime.execute_agent(agent_id="test_agent", context=context)
    events1 = runtime.get_lifecycle_events()
    assert len(events1) > 0

    # Second execution (should replace previous events)
    runtime.execute_agent(agent_id="test_agent", context=context)
    events2 = runtime.get_lifecycle_events()
    assert len(events2) > 0

    # Events should be from the most recent execution
    # (Both should have same structure but may have different run_ids in metadata)
    assert len(events2) >= 3


def test_lifecycle_events_empty_before_execution():
    """Test that lifecycle events return empty list before execution."""
    config = AgentCoreConfig(runtime=RuntimeConfig(runtime_id="test_runtime"))
    runtime = Runtime(config=config)

    # Before any execution, events should be empty
    events = runtime.get_lifecycle_events()
    assert events == []
