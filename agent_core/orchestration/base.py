"""Base flow engine interface.

Defines the abstract interface for flow engine implementations.
All flow engine implementations must conform to this interface.
"""

from abc import ABC, abstractmethod
from typing import Any

from agent_core.configuration.schemas import FlowConfig
from agent_core.contracts.execution_context import ExecutionContext
from agent_core.contracts.flow import Flow, FlowState


class BaseFlowEngine(ABC):
    """Abstract base class for flow engine implementations.

    This class defines the interface that all flow engine implementations
    must conform to. Implementations can use different orchestration
    backends (e.g., simple sequential execution, LangGraph) as long as
    they implement this interface.

    Flow engines must:
    - execute flows deterministically
    - be inspectable and replayable
    - maintain flow state and history
    - emit observability signals
    """

    def __init__(
        self,
        flow: Flow | FlowConfig,
        context: ExecutionContext,
        runtime: Any,  # Runtime type to avoid circular import
    ):
        """Initialize flow engine.

        Args:
            flow: Flow instance or FlowConfig to execute.
            context: Execution context for flow execution.
            runtime: Runtime instance for agent/tool execution.
        """
        self.flow = flow
        self.context = context
        self.runtime = runtime

    @abstractmethod
    def execute(self, input_data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute the flow.

        Executes the flow starting from the entrypoint node, following
        transitions deterministically until completion or error.

        Args:
            input_data: Optional input data for flow execution.

        Returns:
            Dictionary containing execution result with final state and output.

        Raises:
            FlowExecutionError: If flow execution fails.
        """
        ...

    @abstractmethod
    def get_state(self) -> FlowState:
        """Get current flow state.

        Returns:
            Current FlowState instance.
        """
        ...
