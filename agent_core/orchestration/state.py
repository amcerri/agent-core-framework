"""Flow state management.

Provides utilities for managing flow execution state, including
current node tracking, state data accumulation, and execution history.
"""

from typing import Any

from agent_core.contracts.flow import FlowState


class FlowStateManager:
    """Manages flow execution state.

    Tracks current node, accumulated state data, and execution history
    for a flow execution. State is immutable and history is append-only
    to ensure inspectability and replayability.
    """

    def __init__(self, initial_node: str, initial_state: dict[str, Any] | None = None):
        """Initialize flow state manager.

        Args:
            initial_node: Starting node identifier.
            initial_state: Optional initial state data.
        """
        self._current_node = initial_node
        self._state_data = initial_state or {}
        self._history: list[dict[str, Any]] = []

    @property
    def current_node(self) -> str:
        """Current node identifier."""
        return self._current_node

    @property
    def state_data(self) -> dict[str, Any]:
        """Current state data (read-only copy)."""
        return self._state_data.copy()

    @property
    def history(self) -> list[dict[str, Any]]:
        """Execution history (read-only copy)."""
        return self._history.copy()

    def transition_to(self, node_id: str, metadata: dict[str, Any] | None = None) -> None:
        """Transition to a new node.

        Args:
            node_id: Target node identifier.
            metadata: Optional metadata for the transition.
        """
        # Record transition in history
        history_entry = {
            "from_node": self._current_node,
            "to_node": node_id,
            "metadata": metadata or {},
        }
        self._history.append(history_entry)

        # Update current node
        self._current_node = node_id

    def update_state(self, updates: dict[str, Any]) -> None:
        """Update state data.

        Args:
            updates: Dictionary of state updates to merge.
        """
        self._state_data.update(updates)

    def to_flow_state(self) -> FlowState:
        """Convert to FlowState contract.

        Returns:
            FlowState instance representing current state.
        """
        return FlowState(
            current_node=self._current_node,
            state_data=self._state_data.copy(),
            history=self._history.copy(),
        )

    def get_state_snapshot(self) -> dict[str, Any]:
        """Get a snapshot of current state.

        Returns:
            Dictionary containing current node, state data, and history.
        """
        return {
            "current_node": self._current_node,
            "state_data": self._state_data.copy(),
            "history": self._history.copy(),
        }
