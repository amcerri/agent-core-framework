"""Unit tests for FlowStateManager."""

from agent_core.orchestration.state import FlowStateManager


class TestFlowStateManager:
    """Test FlowStateManager."""

    def test_initialization(self):
        """Test FlowStateManager initialization."""
        manager = FlowStateManager(initial_node="start", initial_state={"key": "value"})

        assert manager.current_node == "start"
        assert manager.state_data == {"key": "value"}
        assert len(manager.history) == 0

    def test_transition_to(self):
        """Test node transition."""
        manager = FlowStateManager(initial_node="start")
        manager.transition_to("middle", metadata={"reason": "test"})

        assert manager.current_node == "middle"
        assert len(manager.history) == 1
        assert manager.history[0]["from_node"] == "start"
        assert manager.history[0]["to_node"] == "middle"

    def test_update_state(self):
        """Test state data update."""
        manager = FlowStateManager(initial_node="start", initial_state={"a": 1})
        manager.update_state({"b": 2, "c": 3})

        assert manager.state_data == {"a": 1, "b": 2, "c": 3}

    def test_to_flow_state(self):
        """Test conversion to FlowState."""
        manager = FlowStateManager(initial_node="start", initial_state={"key": "value"})
        manager.transition_to("end")

        flow_state = manager.to_flow_state()

        assert flow_state.current_node == "end"
        assert flow_state.state_data == {"key": "value"}
        assert len(flow_state.history) == 1

    def test_get_state_snapshot(self):
        """Test state snapshot."""
        manager = FlowStateManager(initial_node="start", initial_state={"key": "value"})
        manager.transition_to("end")

        snapshot = manager.get_state_snapshot()

        assert snapshot["current_node"] == "end"
        assert snapshot["state_data"] == {"key": "value"}
        assert len(snapshot["history"]) == 1

    def test_state_data_immutability(self):
        """Test that state_data returns a copy."""
        manager = FlowStateManager(initial_node="start", initial_state={"key": "value"})
        state_copy = manager.state_data

        # Modifying the copy should not affect internal state
        state_copy["new_key"] = "new_value"

        assert "new_key" not in manager.state_data
