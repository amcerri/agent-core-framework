"""Contract tests for Observability schemas."""

import pytest
from pydantic import ValidationError

from agent_core.contracts.observability import (
    AuditEvent,
    ComponentType,
    CorrelationFields,
    LogEvent,
    LogLevel,
    MetricValue,
    SpanAttributes,
    TraceSpan,
)
from agent_core.utils.ids import generate_correlation_id, generate_run_id


class TestCorrelationFields:
    """Test CorrelationFields schema."""

    def test_correlation_fields_creation(self):
        """Test that CorrelationFields can be created with all required fields."""
        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        correlation = CorrelationFields(
            run_id=run_id,
            correlation_id=correlation_id,
            component_type=ComponentType.AGENT,
            component_id="agent:test_agent",
            component_version="1.0.0",
            timestamp="2024-01-01T00:00:00Z",
        )

        assert correlation.run_id == run_id
        assert correlation.correlation_id == correlation_id
        assert correlation.component_type == ComponentType.AGENT
        assert correlation.component_id == "agent:test_agent"
        assert correlation.component_version == "1.0.0"
        assert correlation.timestamp == "2024-01-01T00:00:00Z"

    def test_correlation_fields_requires_all_fields(self):
        """Test that CorrelationFields requires all mandatory fields."""
        with pytest.raises(ValidationError):
            CorrelationFields(
                run_id=generate_run_id(),
                correlation_id=generate_correlation_id(),
            )


class TestLogEvent:
    """Test LogEvent schema."""

    def test_log_event_creation(self):
        """Test that LogEvent can be created with required fields."""
        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        log_event = LogEvent(
            correlation=CorrelationFields(
                run_id=run_id,
                correlation_id=correlation_id,
                component_type=ComponentType.RUNTIME,
                component_id="runtime:main",
                component_version="1.0.0",
                timestamp="2024-01-01T00:00:00Z",
            ),
            level=LogLevel.INFO,
            message="Execution started",
        )

        assert log_event.correlation.run_id == run_id
        assert log_event.level == LogLevel.INFO
        assert log_event.message == "Execution started"
        assert log_event.metadata == {}

    def test_log_event_with_metadata(self):
        """Test that LogEvent can include metadata."""
        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        log_event = LogEvent(
            correlation=CorrelationFields(
                run_id=run_id,
                correlation_id=correlation_id,
                component_type=ComponentType.AGENT,
                component_id="agent:test",
                component_version="1.0.0",
                timestamp="2024-01-01T00:00:00Z",
            ),
            level=LogLevel.WARN,
            message="Budget warning",
            metadata={"remaining_budget": 10},
        )

        assert log_event.metadata == {"remaining_budget": 10}


class TestTraceSpan:
    """Test TraceSpan schema."""

    def test_trace_span_creation(self):
        """Test that TraceSpan can be created with required fields."""
        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        span = TraceSpan(
            correlation=CorrelationFields(
                run_id=run_id,
                correlation_id=correlation_id,
                component_type=ComponentType.AGENT,
                component_id="agent:test",
                component_version="1.0.0",
                timestamp="2024-01-01T00:00:00Z",
            ),
            span_name="agent.execution",
        )

        assert span.span_name == "agent.execution"
        assert span.parent_span_id is None
        assert span.attributes.execution_status is None

    def test_trace_span_with_attributes(self):
        """Test that TraceSpan can include attributes."""
        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        span = TraceSpan(
            correlation=CorrelationFields(
                run_id=run_id,
                correlation_id=correlation_id,
                component_type=ComponentType.TOOL,
                component_id="tool:test",
                component_version="1.0.0",
                timestamp="2024-01-01T00:00:00Z",
            ),
            span_name="tool.invoke",
            attributes=SpanAttributes(
                execution_status="success",
                duration_ms=150.5,
            ),
        )

        assert span.attributes.execution_status == "success"
        assert span.attributes.duration_ms == 150.5


class TestMetricValue:
    """Test MetricValue schema."""

    def test_metric_value_creation(self):
        """Test that MetricValue can be created with required fields."""
        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        metric = MetricValue(
            correlation=CorrelationFields(
                run_id=run_id,
                correlation_id=correlation_id,
                component_type=ComponentType.RUNTIME,
                component_id="runtime:main",
                component_version="1.0.0",
                timestamp="2024-01-01T00:00:00Z",
            ),
            metric_name="execution.count",
            metric_type="counter",
            value=1.0,
        )

        assert metric.metric_name == "execution.count"
        assert metric.metric_type == "counter"
        assert metric.value == 1.0
        assert metric.labels == {}

    def test_metric_value_with_labels(self):
        """Test that MetricValue can include labels."""
        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        metric = MetricValue(
            correlation=CorrelationFields(
                run_id=run_id,
                correlation_id=correlation_id,
                component_type=ComponentType.AGENT,
                component_id="agent:test",
                component_version="1.0.0",
                timestamp="2024-01-01T00:00:00Z",
            ),
            metric_name="latency.histogram",
            metric_type="histogram",
            value=100.0,
            labels={"agent_type": "llm", "status": "success"},
        )

        assert metric.labels == {"agent_type": "llm", "status": "success"}

    def test_metric_value_no_high_cardinality_labels(self):
        """Test that MetricValue does not enforce run_id in labels (enforced by tests/rules)."""
        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        # Note: The schema itself doesn't prevent run_id as a label,
        # but contract tests and runtime enforcement should prevent it.
        # This test documents the expected behavior.
        metric = MetricValue(
            correlation=CorrelationFields(
                run_id=run_id,
                correlation_id=correlation_id,
                component_type=ComponentType.RUNTIME,
                component_id="runtime:main",
                component_version="1.0.0",
                timestamp="2024-01-01T00:00:00Z",
            ),
            metric_name="test.metric",
            metric_type="counter",
            value=1.0,
            labels={"component": "runtime"},  # Low cardinality
        )

        assert "run_id" not in metric.labels
        assert metric.labels == {"component": "runtime"}


class TestAuditEvent:
    """Test AuditEvent schema."""

    def test_audit_event_creation(self):
        """Test that AuditEvent can be created with required fields."""
        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        audit_event = AuditEvent(
            correlation=CorrelationFields(
                run_id=run_id,
                correlation_id=correlation_id,
                component_type=ComponentType.RUNTIME,
                component_id="runtime:governance",
                component_version="1.0.0",
                timestamp="2024-01-01T00:00:00Z",
            ),
            initiator_identity="user:test_user",
            action="tool.execute",
            target_resource="tool:my_tool",
            decision_outcome="allowed",
        )

        assert audit_event.initiator_identity == "user:test_user"
        assert audit_event.action == "tool.execute"
        assert audit_event.target_resource == "tool:my_tool"
        assert audit_event.decision_outcome == "allowed"
        assert audit_event.policy_or_permission is None

    def test_audit_event_with_policy(self):
        """Test that AuditEvent can include policy or permission."""
        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        audit_event = AuditEvent(
            correlation=CorrelationFields(
                run_id=run_id,
                correlation_id=correlation_id,
                component_type=ComponentType.RUNTIME,
                component_id="runtime:governance",
                component_version="1.0.0",
                timestamp="2024-01-01T00:00:00Z",
            ),
            initiator_identity="user:test_user",
            action="service.write",
            target_resource="service:data_service",
            decision_outcome="denied",
            policy_or_permission="policy:write_restriction",
        )

        assert audit_event.policy_or_permission == "policy:write_restriction"


class TestComponentType:
    """Test ComponentType enumeration."""

    def test_all_component_types_available(self):
        """Test that all required component types are available."""
        types = [
            ComponentType.RUNTIME,
            ComponentType.AGENT,
            ComponentType.TOOL,
            ComponentType.SERVICE,
            ComponentType.FLOW,
        ]

        for component_type in types:
            run_id = generate_run_id()
            correlation_id = generate_correlation_id()

            correlation = CorrelationFields(
                run_id=run_id,
                correlation_id=correlation_id,
                component_type=component_type,
                component_id=f"{component_type.value}:test",
                component_version="1.0.0",
                timestamp="2024-01-01T00:00:00Z",
            )

            assert correlation.component_type == component_type
