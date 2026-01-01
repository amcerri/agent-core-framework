"""Unit tests for NoOpObservabilitySink."""

from agent_core.contracts.observability import (
    AuditEvent,
    ComponentType,
    CorrelationFields,
    LogEvent,
    LogLevel,
    MetricValue,
    TraceSpan,
)
from agent_core.observability.noop import NoOpObservabilitySink
from agent_core.utils.ids import generate_correlation_id, generate_run_id


class TestNoOpObservabilitySink:
    """Test NoOpObservabilitySink implementation."""

    def test_noop_sink_implements_interface(self):
        """Test that NoOpObservabilitySink implements ObservabilitySink protocol."""
        sink = NoOpObservabilitySink()

        # Verify it has all required methods
        assert hasattr(sink, "emit_log")
        assert hasattr(sink, "emit_trace")
        assert hasattr(sink, "emit_metric")
        assert hasattr(sink, "emit_audit")

        # Verify methods are callable
        assert callable(sink.emit_log)
        assert callable(sink.emit_trace)
        assert callable(sink.emit_metric)
        assert callable(sink.emit_audit)

    def test_emit_log_noop(self):
        """Test that emit_log is a no-op."""
        sink = NoOpObservabilitySink()

        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        log_event = LogEvent(
            correlation=CorrelationFields(
                run_id=run_id,
                correlation_id=correlation_id,
                component_type=ComponentType.RUNTIME,
                component_id="runtime:test",
                component_version="1.0.0",
                timestamp="2024-01-01T00:00:00Z",
            ),
            level=LogLevel.INFO,
            message="Test log message",
        )

        # Should not raise any exceptions
        sink.emit_log(log_event)

    def test_emit_trace_noop(self):
        """Test that emit_trace is a no-op."""
        sink = NoOpObservabilitySink()

        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        span = TraceSpan(
            correlation=CorrelationFields(
                run_id=run_id,
                correlation_id=correlation_id,
                component_type=ComponentType.AGENT,
                component_id="agent:test_agent",
                component_version="1.0.0",
                timestamp="2024-01-01T00:00:00Z",
            ),
            span_name="agent.execution",
        )

        # Should not raise any exceptions
        sink.emit_trace(span)

    def test_emit_metric_noop(self):
        """Test that emit_metric is a no-op."""
        sink = NoOpObservabilitySink()

        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        metric = MetricValue(
            correlation=CorrelationFields(
                run_id=run_id,
                correlation_id=correlation_id,
                component_type=ComponentType.TOOL,
                component_id="tool:test_tool",
                component_version="1.0.0",
                timestamp="2024-01-01T00:00:00Z",
            ),
            metric_name="execution.count",
            metric_type="counter",
            value=1.0,
        )

        # Should not raise any exceptions
        sink.emit_metric(metric)

    def test_emit_audit_noop(self):
        """Test that emit_audit is a no-op."""
        sink = NoOpObservabilitySink()

        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        audit_event = AuditEvent(
            correlation=CorrelationFields(
                run_id=run_id,
                correlation_id=correlation_id,
                component_type=ComponentType.SERVICE,
                component_id="service:test_service",
                component_version="1.0.0",
                timestamp="2024-01-01T00:00:00Z",
            ),
            initiator_identity="user:test",
            action="service.read",
            target_resource="service:test_service",
            decision_outcome="allowed",
        )

        # Should not raise any exceptions
        sink.emit_audit(audit_event)

    def test_noop_sink_accepts_all_signal_types(self):
        """Test that no-op sink accepts all signal types."""
        sink = NoOpObservabilitySink()

        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        correlation = CorrelationFields(
            run_id=run_id,
            correlation_id=correlation_id,
            component_type=ComponentType.RUNTIME,
            component_id="runtime:test",
            component_version="1.0.0",
            timestamp="2024-01-01T00:00:00Z",
        )

        # Create all signal types
        log_event = LogEvent(
            correlation=correlation,
            level=LogLevel.DEBUG,
            message="Debug message",
        )

        span = TraceSpan(
            correlation=correlation,
            span_name="test.span",
        )

        metric = MetricValue(
            correlation=correlation,
            metric_name="test.metric",
            metric_type="gauge",
            value=42.0,
        )

        audit_event = AuditEvent(
            correlation=correlation,
            initiator_identity="user:test",
            action="test.action",
            target_resource="resource:test",
            decision_outcome="allowed",
        )

        # All should execute without errors
        sink.emit_log(log_event)
        sink.emit_trace(span)
        sink.emit_metric(metric)
        sink.emit_audit(audit_event)
