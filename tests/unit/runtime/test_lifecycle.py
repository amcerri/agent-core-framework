"""Unit tests for lifecycle management."""

import pytest

from agent_core.contracts.execution_context import ExecutionContext
from agent_core.runtime.execution_context import create_execution_context
from agent_core.runtime.lifecycle import LifecycleEvent, LifecycleManager, LifecycleState


class TestLifecycleManager:
    """Test LifecycleManager."""

    def test_initial_state(self):
        """Test that lifecycle starts in INITIALIZING state."""
        context = create_execution_context(initiator="user:test")
        lifecycle = LifecycleManager(context)

        assert lifecycle.get_state() == LifecycleState.INITIALIZING

    def test_transition_to_ready(self):
        """Test transition from INITIALIZING to READY."""
        context = create_execution_context(initiator="user:test")
        lifecycle = LifecycleManager(context)

        lifecycle.transition_to(LifecycleState.READY)

        assert lifecycle.get_state() == LifecycleState.READY
        events = lifecycle.get_events()
        assert len(events) == 1
        assert events[0][0] == LifecycleEvent.INITIALIZATION_COMPLETED

    def test_transition_to_executing(self):
        """Test transition from READY to EXECUTING."""
        context = create_execution_context(initiator="user:test")
        lifecycle = LifecycleManager(context)

        lifecycle.transition_to(LifecycleState.READY)
        lifecycle.transition_to(LifecycleState.EXECUTING)

        assert lifecycle.get_state() == LifecycleState.EXECUTING
        events = lifecycle.get_events()
        assert LifecycleEvent.EXECUTION_STARTED in [e[0] for e in events]

    def test_transition_to_completed(self):
        """Test transition from EXECUTING to COMPLETED."""
        context = create_execution_context(initiator="user:test")
        lifecycle = LifecycleManager(context)

        lifecycle.transition_to(LifecycleState.READY)
        lifecycle.transition_to(LifecycleState.EXECUTING)
        lifecycle.transition_to(LifecycleState.COMPLETED)

        assert lifecycle.get_state() == LifecycleState.COMPLETED
        events = lifecycle.get_events()
        assert LifecycleEvent.EXECUTION_COMPLETED in [e[0] for e in events]

    def test_transition_to_failed(self):
        """Test transition to FAILED state."""
        context = create_execution_context(initiator="user:test")
        lifecycle = LifecycleManager(context)

        lifecycle.transition_to(LifecycleState.READY)
        lifecycle.transition_to(LifecycleState.EXECUTING)
        lifecycle.transition_to(LifecycleState.FAILED, {"error": "test error"})

        assert lifecycle.get_state() == LifecycleState.FAILED
        events = lifecycle.get_events()
        assert LifecycleEvent.EXECUTION_FAILED in [e[0] for e in events]

    def test_invalid_transition(self):
        """Test that invalid transitions raise ValueError."""
        context = create_execution_context(initiator="user:test")
        lifecycle = LifecycleManager(context)

        # Cannot go directly from INITIALIZING to EXECUTING
        with pytest.raises(ValueError, match="Invalid state transition"):
            lifecycle.transition_to(LifecycleState.EXECUTING)

    def test_is_terminal(self):
        """Test that terminal states are correctly identified."""
        context = create_execution_context(initiator="user:test")
        lifecycle = LifecycleManager(context)

        assert not lifecycle.is_terminal()

        lifecycle.transition_to(LifecycleState.READY)
        assert not lifecycle.is_terminal()

        lifecycle.transition_to(LifecycleState.EXECUTING)
        assert not lifecycle.is_terminal()

        lifecycle.transition_to(LifecycleState.COMPLETED)
        assert lifecycle.is_terminal()

    def test_events_include_metadata(self):
        """Test that events include metadata."""
        context = create_execution_context(initiator="user:test")
        lifecycle = LifecycleManager(context)

        lifecycle.transition_to(LifecycleState.READY, {"metadata": "value"})
        lifecycle.transition_to(LifecycleState.EXECUTING, {"step": 1})

        events = lifecycle.get_events()
        assert len(events) >= 2
        # Check that metadata is preserved
        event_dict = {event: metadata for event, metadata in events}
        assert LifecycleEvent.INITIALIZATION_COMPLETED in event_dict
        assert event_dict[LifecycleEvent.INITIALIZATION_COMPLETED]["metadata"] == "value"
        assert LifecycleEvent.EXECUTION_STARTED in event_dict
        assert event_dict[LifecycleEvent.EXECUTION_STARTED]["step"] == 1

    def test_all_lifecycle_events_tracked(self):
        """Test that all lifecycle transitions generate events."""
        context = create_execution_context(initiator="user:test")
        lifecycle = LifecycleManager(context)

        # Complete lifecycle (COMPLETED is terminal, so TERMINATED is only from EXECUTING)
        lifecycle.transition_to(LifecycleState.READY)
        lifecycle.transition_to(LifecycleState.EXECUTING)
        lifecycle.transition_to(LifecycleState.TERMINATED)

        events = lifecycle.get_events()
        event_types = [event for event, _ in events]
        
        assert LifecycleEvent.INITIALIZATION_COMPLETED in event_types
        assert LifecycleEvent.EXECUTION_STARTED in event_types
        assert LifecycleEvent.TERMINATION_STARTED in event_types
        assert len(events) == 3

    def test_events_accessible_after_completion(self):
        """Test that events are accessible after lifecycle completes."""
        context = create_execution_context(initiator="user:test")
        lifecycle = LifecycleManager(context)

        lifecycle.transition_to(LifecycleState.READY)
        lifecycle.transition_to(LifecycleState.EXECUTING)
        lifecycle.transition_to(LifecycleState.COMPLETED)
        
        # Verify lifecycle is terminal
        assert lifecycle.is_terminal()
        
        # Events should still be accessible
        events = lifecycle.get_events()
        assert len(events) == 3
        assert events[0][0] == LifecycleEvent.INITIALIZATION_COMPLETED
        assert events[1][0] == LifecycleEvent.EXECUTION_STARTED
        assert events[2][0] == LifecycleEvent.EXECUTION_COMPLETED

