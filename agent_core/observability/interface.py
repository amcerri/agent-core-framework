"""Observability sink interface.

Defines the protocol for emitting observability signals (logs, traces,
metrics, and audit events). All observability implementations must
conform to this interface.
"""

from typing import Protocol

from agent_core.contracts.observability import (
    AuditEvent,
    LogEvent,
    MetricValue,
    TraceSpan,
)


class ObservabilitySink(Protocol):
    """Protocol for observability sink implementations.

    Observability sinks receive and process observability signals from
    the runtime and components. They must handle all four signal types:
    logs, traces, metrics, and audit events.

    Implementations must:
    - accept all required signal types
    - preserve correlation fields
    - not alter execution semantics
    - handle failures gracefully (detectable, not silent)

    A no-op implementation must exist for testing and local development.
    """

    def emit_log(self, log_event: LogEvent) -> None:
        """Emit a structured log event.

        Args:
            log_event: Structured log event with correlation fields.

        Notes:
            - Log events must include required correlation fields.
            - Sensitive data should be redacted before emission.
            - Failures should be detectable but not alter execution.
        """
        ...

    def emit_trace(self, span: TraceSpan) -> None:
        """Emit a trace span.

        Args:
            span: Trace span with correlation fields and attributes.

        Notes:
            - Spans must include required correlation fields.
            - Parent span relationships must be preserved.
            - Failures should be detectable but not alter execution.
        """
        ...

    def emit_metric(self, metric: MetricValue) -> None:
        """Emit a metric value.

        Args:
            metric: Metric value with correlation fields and labels.

        Notes:
            - Metrics must include required correlation fields.
            - High-cardinality labels (e.g., run_id) must not be used.
            - Failures should be detectable but not alter execution.
        """
        ...

    def emit_audit(self, audit_event: AuditEvent) -> None:
        """Emit an audit event.

        Args:
            audit_event: Audit event with correlation fields and action details.

        Notes:
            - Audit events must include required correlation fields.
            - Audit events cannot be disabled in production.
            - Failures to emit audit events may terminate execution.
        """
        ...
