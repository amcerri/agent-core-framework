"""Runtime lifecycle management.

Defines the execution lifecycle states and transitions for the runtime.
Lifecycle events are observable and deterministic.
"""

from enum import Enum
from typing import Any

from agent_core.contracts.execution_context import ExecutionContext


class LifecycleState(str, Enum):
    """Lifecycle state enumeration.

    Represents the current state of a runtime execution.
    """

    INITIALIZING = "initializing"
    READY = "ready"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"


class LifecycleEvent(str, Enum):
    """Lifecycle event enumeration.

    Represents observable lifecycle events emitted by the runtime.
    """

    INITIALIZATION_STARTED = "initialization_started"
    INITIALIZATION_COMPLETED = "initialization_completed"
    EXECUTION_STARTED = "execution_started"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"
    TERMINATION_STARTED = "termination_started"
    TERMINATION_COMPLETED = "termination_completed"


class LifecycleManager:
    """Manages runtime execution lifecycle.

    Tracks lifecycle state and emits observable lifecycle events.
    Ensures deterministic state transitions.
    """

    def __init__(self, context: ExecutionContext):
        """Initialize lifecycle manager.

        Args:
            context: Execution context for this lifecycle.
        """
        self.context = context
        self.state = LifecycleState.INITIALIZING
        self.events: list[tuple[LifecycleEvent, dict[str, Any]]] = []

    def transition_to(
        self, new_state: LifecycleState, metadata: dict[str, Any] | None = None
    ) -> None:
        """Transition to a new lifecycle state.

        Args:
            new_state: Target lifecycle state.
            metadata: Optional metadata for the transition.

        Raises:
            ValueError: If the transition is invalid.
        """
        if metadata is None:
            metadata = {}

        # Validate state transition
        valid_transitions = {
            LifecycleState.INITIALIZING: [LifecycleState.READY, LifecycleState.FAILED],
            LifecycleState.READY: [LifecycleState.EXECUTING, LifecycleState.TERMINATED],
            LifecycleState.EXECUTING: [
                LifecycleState.COMPLETED,
                LifecycleState.FAILED,
                LifecycleState.TERMINATED,
            ],
            LifecycleState.COMPLETED: [],
            LifecycleState.FAILED: [LifecycleState.TERMINATED],
            LifecycleState.TERMINATED: [],
        }

        if new_state not in valid_transitions.get(self.state, []):
            raise ValueError(
                f"Invalid state transition from {self.state} to {new_state}. "
                f"Valid transitions: {valid_transitions.get(self.state, [])}"
            )

        # Record event
        event_map = {
            LifecycleState.READY: LifecycleEvent.INITIALIZATION_COMPLETED,
            LifecycleState.EXECUTING: LifecycleEvent.EXECUTION_STARTED,
            LifecycleState.COMPLETED: LifecycleEvent.EXECUTION_COMPLETED,
            LifecycleState.FAILED: LifecycleEvent.EXECUTION_FAILED,
            LifecycleState.TERMINATED: LifecycleEvent.TERMINATION_STARTED,
        }

        if new_state in event_map:
            self.events.append((event_map[new_state], metadata))

        self.state = new_state

    def get_state(self) -> LifecycleState:
        """Get current lifecycle state.

        Returns:
            Current lifecycle state.
        """
        return self.state

    def get_events(self) -> list[tuple[LifecycleEvent, dict[str, Any]]]:
        """Get all lifecycle events recorded so far.

        Returns:
            List of (event, metadata) tuples.
        """
        return self.events.copy()

    def is_terminal(self) -> bool:
        """Check if lifecycle is in a terminal state.

        Returns:
            True if state is COMPLETED, FAILED, or TERMINATED.
        """
        return self.state in {
            LifecycleState.COMPLETED,
            LifecycleState.FAILED,
            LifecycleState.TERMINATED,
        }
