"""Action execution for tools and services.

Provides runtime-side execution of actions requested by agents.
Enforces governance (permissions, policies, budgets) before execution
and emits observability signals.
"""

from datetime import datetime, timezone
from typing import Any

from agent_core.configuration.schemas import AgentCoreConfig
from agent_core.contracts.execution_context import ExecutionContext
from agent_core.contracts.observability import ComponentType, CorrelationFields
from agent_core.contracts.service import Service, ServiceInput, ServiceResult
from agent_core.contracts.tool import Tool, ToolInput
from agent_core.governance.audit import AuditEmitter
from agent_core.governance.budget import BudgetEnforcer, BudgetExhaustedError, BudgetTracker
from agent_core.governance.permissions import PermissionError, PermissionEvaluator
from agent_core.governance.policy import PolicyEngine, PolicyOutcome
from agent_core.observability.interface import ObservabilitySink
from agent_core.observability.logging import get_logger


class ActionExecutionError(Exception):
    """Raised when action execution fails.

    This exception indicates that an action could not be executed,
    typically due to governance violations or execution errors.
    """

    pass


class ActionExecutor:
    """Executes actions requested by agents.

    Handles tool and service execution with full governance enforcement.
    All actions must go through this executor; agents cannot call
    tools/services directly.
    """

    def __init__(
        self,
        context: ExecutionContext,
        config: AgentCoreConfig,
        tools: dict[str, Tool],
        services: dict[str, Service],
        sink: ObservabilitySink,
        budget_tracker: BudgetTracker | None = None,
    ):
        """Initialize action executor.

        Args:
            context: Execution context for this execution.
            config: Runtime configuration.
            tools: Dictionary of tool_id -> Tool instances.
            services: Dictionary of service_id -> Service instances.
            sink: Observability sink for emitting signals.
            budget_tracker: Optional budget tracker for tracking consumption.
        """
        self.context = context
        self.config = config
        self.tools = tools
        self.services = services
        self.sink = sink

        # Initialize governance components
        self.permission_evaluator = PermissionEvaluator(context)
        self.policy_engine = PolicyEngine(context, governance_config=config.governance)
        self.audit_emitter = AuditEmitter(context, sink)

        # Initialize budget tracking if tracker provided
        if budget_tracker is not None:
            self.budget_tracker = budget_tracker
            self.budget_enforcer = BudgetEnforcer(
                budget_tracker, governance_config=config.governance
            )
        else:
            self.budget_tracker = None
            self.budget_enforcer = None

        # Create correlation for observability
        correlation = CorrelationFields(
            run_id=context.run_id,
            correlation_id=context.correlation_id,
            component_type=ComponentType.RUNTIME,
            component_id="runtime:action_executor",
            component_version="1.0.0",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self.logger = get_logger("agent_core.runtime.action_execution", correlation)

    def execute_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """Execute a single action requested by an agent.

        Actions can be:
        - Tool invocations: {"type": "tool", "tool_id": "...", "payload": {...}}
        - Service invocations: {"type": "service", "service_id": "...",
          "action": "...", "payload": {...}}

        Args:
            action: Action dictionary with type, resource identifier, and payload.

        Returns:
            Dictionary containing execution result.

        Raises:
            ActionExecutionError: If action execution fails.
        """
        action_type = action.get("type")
        if action_type is None:
            raise ActionExecutionError("Action must specify 'type' field")

        if action_type == "tool":
            return self._execute_tool_action(action)
        elif action_type == "service":
            return self._execute_service_action(action)
        else:
            raise ActionExecutionError(f"Unknown action type: {action_type}")

    def _execute_tool_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool action.

        Args:
            action: Tool action dictionary.

        Returns:
            Dictionary containing tool execution result.

        Raises:
            ActionExecutionError: If tool execution fails.
        """
        tool_id = action.get("tool_id")
        if tool_id is None:
            raise ActionExecutionError("Tool action must specify 'tool_id'")

        # Get tool
        if tool_id not in self.tools:
            raise ActionExecutionError(f"Tool '{tool_id}' is not registered")

        tool = self.tools[tool_id]

        # Check budget before execution
        if self.budget_enforcer is not None:
            try:
                self.budget_enforcer.check_budget()
            except BudgetExhaustedError as e:
                # Emit audit event for budget exhaustion
                try:
                    self.audit_emitter.emit_budget_exhaustion(
                        budget_type=e.budget_type,
                        limit=e.limit,
                        consumed=e.consumed,
                    )
                except Exception:
                    # Audit failure may terminate execution, but we already have budget error
                    pass
                raise ActionExecutionError(f"Budget exhausted: {e}") from e

        # Check permissions
        try:
            self.permission_evaluator.check_permissions(
                required_permissions=tool.permissions_required,
                resource_id=tool_id,
                resource_type="tool",
            )
        except PermissionError as e:
            # Emit audit event for permission denial
            try:
                self.audit_emitter.emit_permission_decision(
                    action="tool.execute",
                    target_resource=f"tool:{tool_id}",
                    decision_outcome="denied",
                    permission=",".join(tool.permissions_required),
                )
            except Exception:
                # Audit failure may terminate execution
                pass
            raise ActionExecutionError(f"Permission denied: {e}") from e

        # Check policy
        policy_outcome = self.policy_engine.evaluate_policy(
            action="tool.execute",
            resource_id=tool_id,
            resource_type="tool",
        )

        if policy_outcome == PolicyOutcome.DENY:
            # Emit audit event for policy denial
            try:
                self.audit_emitter.emit_policy_decision(
                    action="tool.execute",
                    target_resource=f"tool:{tool_id}",
                    decision_outcome="deny",
                    policy="tool.execute",
                )
            except Exception:
                # Audit failure may terminate execution
                pass
            raise ActionExecutionError(f"Policy denied execution of tool '{tool_id}'")

        if policy_outcome == PolicyOutcome.REQUIRE_APPROVAL:
            # Emit audit event for approval requirement
            try:
                self.audit_emitter.emit_policy_decision(
                    action="tool.execute",
                    target_resource=f"tool:{tool_id}",
                    decision_outcome="require_approval",
                    policy="tool.execute",
                )
            except Exception:
                # Audit failure may terminate execution
                pass
            raise ActionExecutionError(f"Tool '{tool_id}' execution requires approval")

        # Emit audit event for permission grant
        try:
            self.audit_emitter.emit_permission_decision(
                action="tool.execute",
                target_resource=f"tool:{tool_id}",
                decision_outcome="allowed",
                permission=",".join(tool.permissions_required),
            )
        except Exception:
            # Audit failure may terminate execution
            pass

        # Record call in budget tracker
        if self.budget_tracker is not None:
            self.budget_tracker.record_call()

        # Prepare tool input
        payload = action.get("payload", {})
        timeout = action.get("timeout")
        retry_policy = action.get("retry_policy")

        tool_input = ToolInput(
            payload=payload,
            timeout=timeout,
            retry_policy=retry_policy,
        )

        # Execute tool
        self.logger.info(
            "Executing tool",
            extra={"tool_id": tool_id, "tool_version": tool.tool_version},
        )

        try:
            tool_result = tool.execute(tool_input, self.context)
        except Exception as e:
            self.logger.error(
                "Tool execution failed",
                extra={"tool_id": tool_id, "error": str(e)},
            )
            raise ActionExecutionError(f"Tool execution failed: {e}") from e

        # Record cost if available in metrics
        if self.budget_tracker is not None and "cost" in tool_result.metrics:
            self.budget_tracker.record_cost(tool_result.metrics["cost"])

        self.logger.info(
            "Tool execution completed",
            extra={
                "tool_id": tool_id,
                "status": tool_result.status,
            },
        )

        # Return result as dictionary
        return {
            "type": "tool",
            "tool_id": tool_id,
            "status": tool_result.status,
            "output": tool_result.output,
            "errors": tool_result.errors,
            "metrics": tool_result.metrics,
        }

    def _execute_service_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """Execute a service action.

        Args:
            action: Service action dictionary.

        Returns:
            Dictionary containing service execution result.

        Raises:
            ActionExecutionError: If service execution fails.
        """
        service_id = action.get("service_id")
        if service_id is None:
            raise ActionExecutionError("Service action must specify 'service_id'")

        service_action = action.get("action")
        if service_action is None:
            raise ActionExecutionError("Service action must specify 'action'")

        # Get service
        if service_id not in self.services:
            raise ActionExecutionError(f"Service '{service_id}' is not registered")

        service = self.services[service_id]

        # Check budget before execution
        if self.budget_enforcer is not None:
            try:
                self.budget_enforcer.check_budget()
            except BudgetExhaustedError as e:
                # Emit audit event for budget exhaustion
                try:
                    self.audit_emitter.emit_budget_exhaustion(
                        budget_type=e.budget_type,
                        limit=e.limit,
                        consumed=e.consumed,
                    )
                except Exception:
                    # Audit failure may terminate execution
                    pass
                raise ActionExecutionError(f"Budget exhausted: {e}") from e

        # Check service permission
        has_permission = service.check_permission(service_action, self.context)

        if not has_permission:
            # Emit audit event for permission denial
            try:
                self.audit_emitter.emit_permission_decision(
                    action=f"service.{service_action}",
                    target_resource=f"service:{service_id}",
                    decision_outcome="denied",
                    permission=service_action,
                )
            except Exception:
                # Audit failure may terminate execution
                pass
            raise ActionExecutionError(
                f"Permission denied for service action '{service_action}' on '{service_id}'"
            )

        # Check policy
        policy_outcome = self.policy_engine.evaluate_policy(
            action=f"service.{service_action}",
            resource_id=service_id,
            resource_type="service",
        )

        if policy_outcome == PolicyOutcome.DENY:
            # Emit audit event for policy denial
            try:
                self.audit_emitter.emit_policy_decision(
                    action=f"service.{service_action}",
                    target_resource=f"service:{service_id}",
                    decision_outcome="deny",
                    policy=f"service.{service_action}",
                )
            except Exception:
                # Audit failure may terminate execution
                pass
            raise ActionExecutionError(
                f"Policy denied service action '{service_action}' on '{service_id}'"
            )

        if policy_outcome == PolicyOutcome.REQUIRE_APPROVAL:
            # Emit audit event for approval requirement
            try:
                self.audit_emitter.emit_policy_decision(
                    action=f"service.{service_action}",
                    target_resource=f"service:{service_id}",
                    decision_outcome="require_approval",
                    policy=f"service.{service_action}",
                )
            except Exception:
                # Audit failure may terminate execution
                pass
            raise ActionExecutionError(
                f"Service action '{service_action}' on '{service_id}' requires approval"
            )

        # Emit audit event for permission grant
        try:
            self.audit_emitter.emit_permission_decision(
                action=f"service.{service_action}",
                target_resource=f"service:{service_id}",
                decision_outcome="allowed",
                permission=service_action,
            )
        except Exception:
            # Audit failure may terminate execution
            pass

        # Record call in budget tracker
        if self.budget_tracker is not None:
            self.budget_tracker.record_call()

        # Prepare service input
        payload = action.get("payload", {})

        service_input = ServiceInput(
            action=service_action,
            payload=payload,
        )

        # Execute service action
        self.logger.info(
            "Executing service action",
            extra={
                "service_id": service_id,
                "service_version": service.service_version,
                "action": service_action,
            },
        )

        try:
            service_result = service.execute(service_input, self.context)
        except Exception as e:
            self.logger.error(
                "Service execution failed",
                extra={"service_id": service_id, "action": service_action, "error": str(e)},
            )
            raise ActionExecutionError(f"Service execution failed: {e}") from e

        # Record cost if available in metrics
        if self.budget_tracker is not None and "cost" in service_result.metrics:
            self.budget_tracker.record_cost(service_result.metrics["cost"])

        self.logger.info(
            "Service action execution completed",
            extra={
                "service_id": service_id,
                "action": service_action,
                "status": service_result.status,
            },
        )

        # Return result as dictionary
        return {
            "type": "service",
            "service_id": service_id,
            "action": service_action,
            "status": service_result.status,
            "output": service_result.output,
            "errors": service_result.errors,
            "metrics": service_result.metrics,
        }
