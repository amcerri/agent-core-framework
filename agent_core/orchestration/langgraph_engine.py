"""LangGraph-backed flow engine implementation.

Provides a LangGraph-based flow engine implementation for executing
declarative flow definitions. All LangGraph types are isolated to
this module to prevent type leakage.

This implementation uses LangGraph as the orchestration backend while
maintaining the same interface as other flow engine implementations.
"""

from datetime import datetime, timezone
from typing import Any

from agent_core.configuration.schemas import FlowConfig
from agent_core.contracts.execution_context import ExecutionContext
from agent_core.contracts.flow import Flow, FlowState
from agent_core.contracts.observability import ComponentType, CorrelationFields
from agent_core.observability.logging import get_logger
from agent_core.orchestration.base import BaseFlowEngine
from agent_core.orchestration.flow_engine import FlowExecutionError
from agent_core.orchestration.state import FlowStateManager

# LangGraph imports are isolated to this module
# Type checking is disabled for LangGraph imports to prevent type leakage
try:
    from langgraph.graph import END, START, StateGraph  # type: ignore[import-untyped]
    from langgraph.graph.message import add_messages  # type: ignore[import-untyped]

    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    # Create dummy types for type checking when LangGraph is not available
    StateGraph = Any  # type: ignore[assignment, misc]
    START = "__start__"  # type: ignore[assignment]
    END = "__end__"  # type: ignore[assignment]
    add_messages = None  # type: ignore[assignment]


class LangGraphFlowEngine(BaseFlowEngine):
    """LangGraph-backed flow engine implementation.

    Executes flows using LangGraph as the orchestration backend.
    All LangGraph-specific types are isolated to this implementation
    and do not leak outside the orchestration package.

    This implementation provides the same interface as SimpleFlowEngine
    but uses LangGraph for more advanced orchestration features.
    """

    def __init__(
        self,
        flow: Flow | FlowConfig,
        context: ExecutionContext,
        runtime: Any,  # Runtime type to avoid circular import
    ):
        """Initialize LangGraph flow engine.

        Args:
            flow: Flow instance or FlowConfig to execute.
            context: Execution context for flow execution.
            runtime: Runtime instance for agent/tool execution.

        Raises:
            FlowExecutionError: If LangGraph is not available.
        """
        super().__init__(flow, context, runtime)

        if not LANGGRAPH_AVAILABLE:
            raise FlowExecutionError(
                "LangGraph is not available. Install langgraph to use LangGraphFlowEngine."
            )

        # Convert FlowConfig to Flow-like interface if needed
        if isinstance(flow, FlowConfig):
            self._flow_config = flow
            self._flow = None
        else:
            self._flow = flow
            self._flow_config = None

        # Get flow properties
        if self._flow_config:
            self.flow_id = self._flow_config.flow_id
            self.flow_version = self._flow_config.version
            self.entrypoint = self._flow_config.entrypoint
            self.nodes = self._flow_config.nodes
            self.transitions = self._flow_config.transitions
        else:
            self.flow_id = self._flow.flow_id
            self.flow_version = self._flow.flow_version
            self.entrypoint = self._flow.entrypoint
            self.nodes = self._flow.nodes
            self.transitions = self._flow.transitions

        # Initialize state manager
        self.state_manager = FlowStateManager(
            initial_node=self.entrypoint,
            initial_state={},
        )

        # Create correlation for observability
        correlation = CorrelationFields(
            run_id=context.run_id,
            correlation_id=context.correlation_id,
            component_type=ComponentType.FLOW,
            component_id=f"flow:{self.flow_id}",
            component_version=self.flow_version,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self.logger = get_logger("agent_core.orchestration.langgraph_engine", correlation)

        # Build LangGraph graph
        self._graph = self._build_graph()

    def _build_graph(self) -> Any:  # StateGraph type, but Any to prevent type leakage
        """Build LangGraph graph from flow definition.

        Returns:
            LangGraph StateGraph instance.
        """
        # Define state schema for LangGraph
        # Use a simple dict-based state that maps to our FlowState
        from typing import TypedDict

        class FlowGraphState(TypedDict):
            """LangGraph state schema."""

            current_node: str
            state_data: dict[str, Any]
            history: list[dict[str, Any]]

        # Create graph
        graph = StateGraph(FlowGraphState)

        # Add nodes to graph
        for node_id, node_def in self.nodes.items():
            graph.add_node(node_id, self._create_node_function(node_id, node_def))

        # Add edges based on transitions
        # Start from entrypoint
        graph.set_entry_point(self.entrypoint)

        # Add transitions
        for transition in self.transitions:
            from_node = transition.get("from")
            to_node = transition.get("to")

            if from_node is None or to_node is None:
                continue

            # Handle conditional edges
            condition = transition.get("condition")
            if condition is not None:
                # Add conditional edge
                graph.add_conditional_edges(
                    from_node,
                    self._create_condition_function(condition),
                    {
                        True: to_node,
                        False: END,  # type: ignore[dict-item]
                    },
                )
            else:
                # Add direct edge
                graph.add_edge(from_node, to_node)

        # Compile graph
        return graph.compile()

    def _create_node_function(self, node_id: str, node_def: dict[str, Any]) -> Any:
        """Create a node function for LangGraph.

        Args:
            node_id: Node identifier.
            node_def: Node definition.

        Returns:
            Node function for LangGraph.
        """

        def node_function(state: dict[str, Any]) -> dict[str, Any]:
            """Execute node and return updated state."""
            # Execute node using the same logic as SimpleFlowEngine
            node_result = self._execute_node(node_id, node_def)

            # Update state
            state_data = state.get("state_data", {})
            state_data[f"node_{node_id}_result"] = node_result
            updated_state = {
                "current_node": node_id,
                "state_data": state_data,
                "history": state.get("history", []) + [{"node_id": node_id, "result": node_result}],
            }

            return updated_state

        return node_function

    def _create_condition_function(self, condition: dict[str, Any]) -> Any:
        """Create a condition function for LangGraph conditional edges.

        Args:
            condition: Condition definition.

        Returns:
            Condition function for LangGraph.
        """

        def condition_function(state: dict[str, Any]) -> bool:
            """Evaluate condition and return True/False."""
            # Evaluate condition based on state
            state_data = state.get("state_data", {})
            return self._evaluate_transition_condition(condition, state_data)

        return condition_function

    def execute(self, input_data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute the flow using LangGraph.

        Args:
            input_data: Optional input data for flow execution.

        Returns:
            Dictionary containing execution result with final state and output.

        Raises:
            FlowExecutionError: If flow execution fails.
        """
        if input_data is None:
            input_data = {}

        # Initialize state with input data
        self.state_manager.update_state({"input": input_data})

        self.logger.info(
            "Flow execution started (LangGraph)",
            extra={
                "flow_id": self.flow_id,
                "entrypoint": self.entrypoint,
            },
        )

        try:
            # Prepare initial state for LangGraph
            initial_state: dict[str, Any] = {
                "current_node": self.entrypoint,
                "state_data": {"input": input_data},
                "history": [],
            }

            # Execute graph
            final_state = self._graph.invoke(initial_state)

            # Update state manager with final state
            self.state_manager._current_node = final_state.get("current_node", self.entrypoint)
            self.state_manager._state_data = final_state.get("state_data", {})
            self.state_manager._history = final_state.get("history", [])

            self.logger.info(
                "Flow execution completed (LangGraph)",
                extra={
                    "flow_id": self.flow_id,
                    "final_node": final_state.get("current_node"),
                },
            )

            # Return final state and output
            return {
                "status": "completed",
                "flow_id": self.flow_id,
                "final_node": final_state.get("current_node"),
                "state": final_state.get("state_data", {}),
                "history": final_state.get("history", []),
            }

        except Exception as e:
            self.logger.error(
                "Flow execution failed (LangGraph)",
                extra={
                    "flow_id": self.flow_id,
                    "error": str(e),
                },
            )
            raise FlowExecutionError(f"Flow execution failed: {e}") from e

    def _execute_node(self, node_id: str, node_def: dict[str, Any]) -> dict[str, Any]:
        """Execute a single node.

        Args:
            node_id: Node identifier.
            node_def: Node definition dictionary.

        Returns:
            Node execution result.

        Raises:
            FlowExecutionError: If node execution fails.
        """
        node_type = node_def.get("type", "agent")

        if node_type == "agent":
            return self._execute_agent_node(node_id, node_def)
        elif node_type == "tool":
            return self._execute_tool_node(node_id, node_def)
        elif node_type == "condition":
            return self._execute_condition_node(node_id, node_def)
        else:
            raise FlowExecutionError(f"Unknown node type: {node_type}")

    def _execute_agent_node(self, node_id: str, node_def: dict[str, Any]) -> dict[str, Any]:
        """Execute an agent node."""
        agent_id = node_def.get("agent_id")
        if agent_id is None:
            raise FlowExecutionError(f"Agent node '{node_id}' missing 'agent_id'")

        input_data = node_def.get("input", {})
        if "input_from_state" in node_def:
            state_keys = node_def["input_from_state"]
            for key in state_keys:
                if key in self.state_manager.state_data:
                    input_data[key] = self.state_manager.state_data[key]

        result = self.runtime.execute_agent(
            agent_id=agent_id,
            input_data=input_data,
            context=self.context,
        )

        return {
            "type": "agent",
            "agent_id": agent_id,
            "status": result.status,
            "output": result.output,
            "actions": result.actions,
        }

    def _execute_tool_node(self, node_id: str, node_def: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool node."""
        tool_id = node_def.get("tool_id")
        if tool_id is None:
            raise FlowExecutionError(f"Tool node '{node_id}' missing 'tool_id'")

        payload = node_def.get("payload", {})
        if "input_from_state" in node_def:
            state_keys = node_def["input_from_state"]
            for key in state_keys:
                if key in self.state_manager.state_data:
                    payload[key] = self.state_manager.state_data[key]

        action = {
            "type": "tool",
            "tool_id": tool_id,
            "payload": payload,
        }

        # Execute tool via runtime's action executor
        # This ensures flow execution uses the same observability sink and
        # governance configuration as direct execution
        result = self.runtime.execute_action(action, self.context)

        return {
            "type": "tool",
            "tool_id": tool_id,
            "status": result["status"],
            "output": result["output"],
        }

    def _execute_condition_node(self, node_id: str, node_def: dict[str, Any]) -> dict[str, Any]:
        """Execute a condition node."""
        condition = node_def.get("condition")
        if condition is None:
            raise FlowExecutionError(f"Condition node '{node_id}' missing 'condition'")

        state = self.state_manager.state_data

        if isinstance(condition, str):
            result = condition in state and bool(state[condition])
        elif isinstance(condition, dict):
            result = all(state.get(k) == v for k, v in condition.items())
        else:
            result = bool(condition)

        return {
            "type": "condition",
            "result": result,
            "condition": condition,
        }

    def _evaluate_transition_condition(
        self, condition: dict[str, Any], state_data: dict[str, Any]
    ) -> bool:
        """Evaluate a transition condition."""
        if isinstance(condition, dict):
            return all(state_data.get(k) == v for k, v in condition.items())

        return bool(condition)

    def get_state(self) -> FlowState:
        """Get current flow state.

        Returns:
            Current FlowState instance.
        """
        return self.state_manager.to_flow_state()
