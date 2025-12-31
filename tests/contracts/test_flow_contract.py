"""Contract tests for Flow interface and schemas."""

import pytest
from pydantic import ValidationError

from agent_core.contracts.flow import Flow, FlowState


class TestFlowStateSchema:
    """Test FlowState schema validation."""

    def test_flow_state_creation_with_current_node(self):
        """Test that FlowState can be created with current_node."""
        state = FlowState(current_node="node_1")

        assert state.current_node == "node_1"
        assert state.state_data == {}
        assert state.history == []

    def test_flow_state_creation_with_all_fields(self):
        """Test that FlowState can be created with all fields."""
        state = FlowState(
            current_node="node_2",
            state_data={"key": "value"},
            history=[{"node": "node_1", "timestamp": "2024-01-01"}],
        )

        assert state.current_node == "node_2"
        assert state.state_data == {"key": "value"}
        assert len(state.history) == 1

    def test_flow_state_requires_current_node(self):
        """Test that FlowState requires current_node field."""
        with pytest.raises(ValidationError):
            FlowState()


class TestFlowProtocol:
    """Test Flow protocol interface."""

    def test_flow_protocol_can_be_implemented(self):
        """Test that a class can implement the Flow protocol."""

        class MockFlow:
            @property
            def flow_id(self) -> str:
                return "test_flow"

            @property
            def flow_version(self) -> str:
                return "1.0.0"

            @property
            def entrypoint(self) -> str:
                return "start"

            @property
            def nodes(self) -> dict[str, dict[str, str]]:
                return {
                    "start": {"type": "agent", "agent_id": "agent_1"},
                    "end": {"type": "terminal"},
                }

            @property
            def transitions(self) -> list[dict[str, str]]:
                return [
                    {"from": "start", "to": "end", "condition": "success"},
                ]

        flow: Flow = MockFlow()

        assert flow.flow_id == "test_flow"
        assert flow.flow_version == "1.0.0"
        assert flow.entrypoint == "start"
        assert len(flow.nodes) == 2
        assert len(flow.transitions) == 1
