"""No-op observability sink implementation.

Provides a no-op implementation of the ObservabilitySink interface
for testing and local development. All methods are implemented but
do nothing, allowing the framework to run without external observability
backends.
"""

from agent_core.contracts.observability import (
    AuditEvent,
    LogEvent,
    MetricValue,
    TraceSpan,
)
from agent_core.observability.interface import ObservabilitySink


class NoOpObservabilitySink:
    """No-op observability sink implementation.

    This sink implements the ObservabilitySink protocol but discards
    all signals. It is intended for:
    - unit and integration testing
    - local development without observability backends
    - scenarios where observability is not required

    All methods are implemented as no-ops and return immediately.
    """

    def emit_log(self, log_event: LogEvent) -> None:
        """Emit a log event (no-op).

        Args:
            log_event: Structured log event (discarded).
        """
        pass

    def emit_trace(self, span: TraceSpan) -> None:
        """Emit a trace span (no-op).

        Args:
            span: Trace span (discarded).
        """
        pass

    def emit_metric(self, metric: MetricValue) -> None:
        """Emit a metric value (no-op).

        Args:
            metric: Metric value (discarded).
        """
        pass

    def emit_audit(self, audit_event: AuditEvent) -> None:
        """Emit an audit event (no-op).

        Args:
            audit_event: Audit event (discarded).

        Notes:
            In production, audit events should not use a no-op sink.
            This implementation is for testing only.
        """
        pass

