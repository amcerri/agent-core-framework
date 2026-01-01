"""Audit event emission for governance decisions.

Provides audit event emission as a governance responsibility.
Audit events are delivered via the observability sink and cannot
be disabled in production. Audit failures may terminate execution.
"""

from datetime import datetime, timezone

from agent_core.contracts.execution_context import ExecutionContext
from agent_core.contracts.observability import (
    AuditEvent,
    ComponentType,
    CorrelationFields,
)
from agent_core.observability.interface import ObservabilitySink


class AuditEmissionError(Exception):
    """Raised when audit emission fails.

    This exception indicates that an audit event could not be emitted,
    which may require terminating execution per audit rules.
    """

    pass


class AuditEmitter:
    """Emits audit events for governance decisions.

    Creates and emits audit events via the observability sink for
    all governed decisions (permissions, policies, budgets).
    Audit emission is mandatory and failures may terminate execution.

    Error handling:
    - All audit emission methods raise AuditEmissionError if emission fails.
    - Audit failures may terminate execution per audit rules.
    - In ActionExecutor, audit failures are caught but not re-raised when
      another error is already being raised, to prevent masking the original
      governance violation.

    Example:
        ```python
        emitter = AuditEmitter(context=execution_context, sink=observability_sink)

        # Emit permission decision
        emitter.emit_permission_decision(
            action="tool.execute",
            target_resource="tool:my_tool",
            decision_outcome="allowed",
            permission="read",
        )
        ```
    """

    def __init__(
        self,
        context: ExecutionContext,
        sink: ObservabilitySink,
    ):
        """Initialize audit emitter.

        Args:
            context: Execution context for correlation fields.
            sink: Observability sink for emitting audit events.
        """
        self.context = context
        self.sink = sink

    def emit_permission_decision(
        self,
        action: str,
        target_resource: str,
        decision_outcome: str,
        permission: str | None = None,
    ) -> None:
        """Emit audit event for a permission decision.

        Args:
            action: Action performed (e.g., 'tool.execute').
            target_resource: Target resource identifier (e.g., 'tool:my_tool').
            decision_outcome: Decision outcome ('allowed' or 'denied').
            permission: Optional permission identifier involved.

        Raises:
            AuditEmissionError: If audit emission fails.
        """
        correlation = CorrelationFields(
            run_id=self.context.run_id,
            correlation_id=self.context.correlation_id,
            component_type=ComponentType.RUNTIME,
            component_id="governance:permissions",
            component_version="1.0.0",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        audit_event = AuditEvent(
            correlation=correlation,
            initiator_identity=self.context.initiator,
            action=action,
            target_resource=target_resource,
            decision_outcome=decision_outcome,
            policy_or_permission=permission,
        )

        try:
            self.sink.emit_audit(audit_event)
        except Exception as e:
            # Audit failures may terminate execution per audit rules
            raise AuditEmissionError(
                f"Failed to emit audit event for permission decision: {e}"
            ) from e

    def emit_policy_decision(
        self,
        action: str,
        target_resource: str,
        decision_outcome: str,
        policy: str | None = None,
    ) -> None:
        """Emit audit event for a policy decision.

        Args:
            action: Action performed (e.g., 'tool.execute').
            target_resource: Target resource identifier (e.g., 'tool:my_tool').
            decision_outcome: Decision outcome ('allow', 'deny', 'require_approval').
            policy: Optional policy identifier involved.

        Raises:
            AuditEmissionError: If audit emission fails.
        """
        correlation = CorrelationFields(
            run_id=self.context.run_id,
            correlation_id=self.context.correlation_id,
            component_type=ComponentType.RUNTIME,
            component_id="governance:policy",
            component_version="1.0.0",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        audit_event = AuditEvent(
            correlation=correlation,
            initiator_identity=self.context.initiator,
            action=action,
            target_resource=target_resource,
            decision_outcome=decision_outcome,
            policy_or_permission=policy,
        )

        try:
            self.sink.emit_audit(audit_event)
        except Exception as e:
            # Audit failures may terminate execution per audit rules
            raise AuditEmissionError(f"Failed to emit audit event for policy decision: {e}") from e

    def emit_budget_exhaustion(
        self,
        budget_type: str,
        limit: float,
        consumed: float,
    ) -> None:
        """Emit audit event for budget exhaustion.

        Args:
            budget_type: Type of budget exhausted ('time', 'calls', 'cost').
            limit: Budget limit that was exceeded.
            consumed: Amount consumed that exceeded the limit.

        Raises:
            AuditEmissionError: If audit emission fails.
        """
        correlation = CorrelationFields(
            run_id=self.context.run_id,
            correlation_id=self.context.correlation_id,
            component_type=ComponentType.RUNTIME,
            component_id="governance:budget",
            component_version="1.0.0",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        action = f"budget.exhausted.{budget_type}"
        target_resource = f"budget:{budget_type}"
        decision_outcome = "denied"

        audit_event = AuditEvent(
            correlation=correlation,
            initiator_identity=self.context.initiator,
            action=action,
            target_resource=target_resource,
            decision_outcome=decision_outcome,
            policy_or_permission=None,
        )

        try:
            self.sink.emit_audit(audit_event)
        except Exception as e:
            # Audit failures may terminate execution per audit rules
            raise AuditEmissionError(
                f"Failed to emit audit event for budget exhaustion: {e}"
            ) from e

    def emit_governance_decision(
        self,
        action: str,
        target_resource: str,
        decision_outcome: str,
        policy_or_permission: str | None = None,
        component_id: str = "governance:general",
    ) -> None:
        """Emit audit event for a general governance decision.

        Generic method for emitting audit events for any governance decision.

        Args:
            action: Action performed.
            target_resource: Target resource identifier.
            decision_outcome: Decision outcome.
            policy_or_permission: Optional policy or permission identifier.
            component_id: Component identifier for correlation.

        Raises:
            AuditEmissionError: If audit emission fails.
        """
        correlation = CorrelationFields(
            run_id=self.context.run_id,
            correlation_id=self.context.correlation_id,
            component_type=ComponentType.RUNTIME,
            component_id=component_id,
            component_version="1.0.0",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        audit_event = AuditEvent(
            correlation=correlation,
            initiator_identity=self.context.initiator,
            action=action,
            target_resource=target_resource,
            decision_outcome=decision_outcome,
            policy_or_permission=policy_or_permission,
        )

        try:
            self.sink.emit_audit(audit_event)
        except Exception as e:
            # Audit failures may terminate execution per audit rules
            raise AuditEmissionError(
                f"Failed to emit audit event for governance decision: {e}"
            ) from e
