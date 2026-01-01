"""Simple flow engine implementation.

Provides a simple sequential flow engine implementation for executing
declarative flow definitions. Flows are deterministic, inspectable,
and replayable.

This is the default implementation. Alternative implementations (e.g.,
LangGraph-backed) can be used by implementing the BaseFlowEngine interface.
"""

import re
from datetime import datetime, timezone
from typing import Any

from agent_core.configuration.schemas import FlowConfig
from agent_core.contracts.execution_context import ExecutionContext
from agent_core.contracts.flow import Flow, FlowState
from agent_core.contracts.observability import ComponentType, CorrelationFields
from agent_core.observability.logging import get_logger
from agent_core.orchestration.base import BaseFlowEngine
from agent_core.orchestration.state import FlowStateManager


class FlowExecutionError(Exception):
    """Raised when flow execution fails.

    This exception indicates that flow execution encountered an error,
    such as invalid node reference, transition failure, or execution error.
    """

    pass


class SimpleFlowEngine(BaseFlowEngine):
    """Simple sequential flow engine implementation.

    Executes flows step by step according to declared transitions.
    Flow execution is deterministic, inspectable, and replayable.

    This is a simple implementation that executes nodes sequentially.
    For more advanced orchestration features, use LangGraphFlowEngine.
    """

    def __init__(
        self,
        flow: Flow | FlowConfig,
        context: ExecutionContext,
        runtime: Any,  # Runtime type to avoid circular import
    ):
        """Initialize simple flow engine.

        Args:
            flow: Flow instance or FlowConfig to execute.
            context: Execution context for flow execution.
            runtime: Runtime instance for agent/tool execution.
        """
        super().__init__(flow, context, runtime)

        # Convert FlowConfig to Flow-like interface if needed
        if isinstance(flow, FlowConfig):
            self._flow_config = flow
            self._flow = None
        else:
            self._flow = flow
            self._flow_config = None

        self.context = context
        self.runtime = runtime

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
        self.logger = get_logger("agent_core.orchestration.flow_engine", correlation)

    def _resolve_template(self, template: str, state_data: dict[str, Any]) -> Any:
        """Resolve template variables in a string.

        Supports:
        - {{input.key}} - resolves to input_data[key]
        - {{node_nodeid_result.key}} - resolves to node result data
        - {{node_nodeid_result.output.key}} - resolves to nested node output

        Args:
            template: Template string with {{variable}} placeholders.
            state_data: Current state data containing input and node results.

        Returns:
            Resolved value (string or original type if no templates found).
        """
        if not isinstance(template, str):
            return template

        # Pattern to match {{variable}} or {{variable.path}}
        pattern = r"\{\{([^}]+)\}\}"

        def replace_match(match: re.Match[str]) -> str:
            var_path = match.group(1).strip()
            parts = var_path.split(".")

            # Handle input.*
            if parts[0] == "input":
                if len(parts) == 1:
                    return str(state_data.get("input", {}))
                value = state_data.get("input", {})
                for part in parts[1:]:
                    if isinstance(value, dict):
                        value = value.get(part)
                    else:
                        return match.group(0)  # Return original if path invalid
                return str(value) if value is not None else ""

            # Handle node_*_result.*
            if parts[0].startswith("node_") and parts[0].endswith("_result"):
                node_id = parts[0][5:-7]  # Remove "node_" prefix and "_result" suffix
                result_key = f"node_{node_id}_result"
                value = state_data.get(result_key, {})
                if len(parts) == 1:
                    return str(value)
                # Navigate through result structure
                for part in parts[1:]:
                    if isinstance(value, dict):
                        value = value.get(part)
                    else:
                        return match.group(0)  # Return original if path invalid
                return str(value) if value is not None else ""

            # Unknown variable - return original
            return match.group(0)

        # Check if template contains any variables
        if not re.search(pattern, template):
            return template

        # Replace all matches
        resolved = re.sub(pattern, replace_match, template)

        # If entire template was a single variable, try to return original type
        single_match = re.match(r"^\{\{([^}]+)\}\}$", template)
        if single_match:
            var_path = single_match.group(1).strip()
            parts = var_path.split(".")
            if parts[0] == "input":
                value = state_data.get("input", {})
                for part in parts[1:]:
                    if isinstance(value, dict):
                        value = value.get(part)
                    else:
                        break
                if value is not None:
                    return value
            elif parts[0].startswith("node_") and parts[0].endswith("_result"):
                node_id = parts[0][5:-7]
                result_key = f"node_{node_id}_result"
                value = state_data.get(result_key, {})
                for part in parts[1:]:
                    if isinstance(value, dict):
                        value = value.get(part)
                    else:
                        break
                if value is not None:
                    return value

        return resolved

    def _resolve_templates_in_dict(
        self, data: dict[str, Any], state_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Recursively resolve template variables in a dictionary.

        Args:
            data: Dictionary that may contain template strings.
            state_data: Current state data for template resolution.

        Returns:
            Dictionary with all template variables resolved.
        """
        resolved = {}
        for key, value in data.items():
            if isinstance(value, dict):
                resolved[key] = self._resolve_templates_in_dict(value, state_data)
            elif isinstance(value, list):
                resolved[key] = [
                    self._resolve_templates_in_dict(item, state_data)
                    if isinstance(item, dict)
                    else self._resolve_template(item, state_data)
                    if isinstance(item, str)
                    else item
                    for item in value
                ]
            elif isinstance(value, str):
                resolved[key] = self._resolve_template(value, state_data)
            else:
                resolved[key] = value
        return resolved

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
        if input_data is None:
            input_data = {}

        # Initialize state with input data
        self.state_manager.update_state({"input": input_data})

        self.logger.info(
            "Flow execution started",
            extra={
                "flow_id": self.flow_id,
                "entrypoint": self.entrypoint,
            },
        )

        try:
            # Execute flow starting from entrypoint
            current_node_id = self.entrypoint
            max_iterations = 100  # Prevent infinite loops
            iteration = 0

            while iteration < max_iterations:
                iteration += 1

                # Check if current node exists
                if current_node_id not in self.nodes:
                    raise FlowExecutionError(
                        f"Node '{current_node_id}' not found in flow '{self.flow_id}'"
                    )

                # Get node definition
                node_def = self.nodes[current_node_id]

                self.logger.debug(
                    "Executing node",
                    extra={
                        "node_id": current_node_id,
                        "iteration": iteration,
                    },
                )

                # Execute node
                node_result = self._execute_node(current_node_id, node_def)

                # Update state with node result
                self.state_manager.update_state({f"node_{current_node_id}_result": node_result})

                # Record node execution in history
                self.state_manager._history.append(
                    {
                        "node_id": current_node_id,
                        "result": node_result,
                        "iteration": iteration,
                    }
                )

                # Find next node based on transitions
                next_node_id = self._find_next_node(current_node_id, node_result)

                if next_node_id is None:
                    # Flow completed (no more transitions)
                    self.logger.info(
                        "Flow execution completed",
                        extra={
                            "flow_id": self.flow_id,
                            "final_node": current_node_id,
                            "iterations": iteration,
                        },
                    )
                    break

                # Transition to next node
                self.state_manager.transition_to(next_node_id)
                current_node_id = next_node_id

            if iteration >= max_iterations:
                raise FlowExecutionError(
                    f"Flow '{self.flow_id}' exceeded maximum iterations ({max_iterations})"
                )

            # Return final state and output
            final_state = self.state_manager.to_flow_state()
            return {
                "status": "completed",
                "flow_id": self.flow_id,
                "final_node": final_state.current_node,
                "state": final_state.state_data,
                "history": final_state.history,
            }

        except FlowExecutionError:
            raise
        except Exception as e:
            self.logger.error(
                "Flow execution failed",
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
        """Execute an agent node.

        Args:
            node_id: Node identifier.
            node_def: Node definition.

        Returns:
            Agent execution result.
        """
        agent_id = node_def.get("agent_id")
        if agent_id is None:
            raise FlowExecutionError(f"Agent node '{node_id}' missing 'agent_id'")

        # Get input from state or node definition
        input_data = node_def.get("input", {})
        # Merge with state data if specified
        if "input_from_state" in node_def:
            state_keys = node_def["input_from_state"]
            for key in state_keys:
                if key in self.state_manager.state_data:
                    input_data[key] = self.state_manager.state_data[key]

        # Resolve template variables in input_data
        state_data = self.state_manager.state_data
        input_data = self._resolve_templates_in_dict(input_data, state_data)

        # Execute agent via runtime
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
        """Execute a tool node.

        Args:
            node_id: Node identifier.
            node_def: Node definition.

        Returns:
            Tool execution result.
        """
        tool_id = node_def.get("tool_id")
        if tool_id is None:
            raise FlowExecutionError(f"Tool node '{node_id}' missing 'tool_id'")

        # Get input from state or node definition
        payload = node_def.get("payload", {})
        # Merge with state data if specified
        if "input_from_state" in node_def:
            state_keys = node_def["input_from_state"]
            for key in state_keys:
                if key in self.state_manager.state_data:
                    payload[key] = self.state_manager.state_data[key]

        # Resolve template variables in payload
        state_data = self.state_manager.state_data
        payload = self._resolve_templates_in_dict(payload, state_data)

        # Create action for tool execution
        action = {
            "type": "tool",
            "tool_id": tool_id,
            "payload": payload,
        }

        # Execute tool via runtime's action executor
        # Note: This requires access to runtime's action executor
        # For now, we'll use a simplified approach
        # In a full implementation, we'd use runtime.execute_action() or similar
        from agent_core.governance.budget import BudgetTracker
        from agent_core.observability.noop import NoOpObservabilitySink
        from agent_core.runtime.action_execution import ActionExecutor

        budget_tracker = BudgetTracker(self.context)
        action_executor = ActionExecutor(
            context=self.context,
            config=self.runtime.config,
            tools=self.runtime.tools,
            services=self.runtime.services,
            sink=NoOpObservabilitySink(),  # Use runtime's sink in full implementation
            budget_tracker=budget_tracker,
        )

        result = action_executor.execute_action(action)

        return {
            "type": "tool",
            "tool_id": tool_id,
            "status": result["status"],
            "output": result["output"],
        }

    def _execute_condition_node(self, node_id: str, node_def: dict[str, Any]) -> dict[str, Any]:
        """Execute a condition node.

        Args:
            node_id: Node identifier.
            node_def: Node definition.

        Returns:
            Condition evaluation result.
        """
        condition = node_def.get("condition")
        if condition is None:
            raise FlowExecutionError(f"Condition node '{node_id}' missing 'condition'")

        # Evaluate condition based on state
        # Simple condition evaluation (can be extended)
        state = self.state_manager.state_data

        # Support simple key-based conditions
        if isinstance(condition, str):
            # Check if key exists in state
            result = condition in state and bool(state[condition])
        elif isinstance(condition, dict):
            # Support more complex conditions (e.g., {"key": "value"})
            result = all(state.get(k) == v for k, v in condition.items())
        else:
            result = bool(condition)

        return {
            "type": "condition",
            "result": result,
            "condition": condition,
        }

    def _find_next_node(self, current_node_id: str, node_result: dict[str, Any]) -> str | None:
        """Find the next node based on transitions.

        Args:
            current_node_id: Current node identifier.
            node_result: Result from current node execution.

        Returns:
            Next node identifier, or None if flow should terminate.
        """
        # Find transitions from current node
        for transition in self.transitions:
            from_node = transition.get("from")
            if from_node != current_node_id:
                continue

            # Check condition if present
            condition = transition.get("condition")
            if condition is not None:
                # Evaluate condition based on node result or state
                if not self._evaluate_transition_condition(condition, node_result):
                    continue

            # Return target node
            to_node = transition.get("to")
            if to_node is None:
                continue

            return to_node

        # No matching transition found - flow terminates
        return None

    def _evaluate_transition_condition(
        self, condition: dict[str, Any], node_result: dict[str, Any]
    ) -> bool:
        """Evaluate a transition condition.

        Args:
            condition: Condition definition.
            node_result: Result from node execution.

        Returns:
            True if condition is met, False otherwise.
        """
        # Simple condition evaluation
        # Support conditions like {"status": "success"} or {"key": "value"}
        if isinstance(condition, dict):
            return all(node_result.get(k) == v for k, v in condition.items())

        return bool(condition)

    def get_state(self) -> FlowState:
        """Get current flow state.

        Returns:
            Current FlowState instance.
        """
        return self.state_manager.to_flow_state()
