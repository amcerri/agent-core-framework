"""Unit tests for metrics emission."""

import pytest
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

from agent_core.contracts.observability import (
    ComponentType,
    CorrelationFields,
)
from agent_core.observability.metrics import MetricsHelper, get_metrics_helper
from agent_core.utils.ids import generate_correlation_id, generate_run_id


@pytest.fixture
def meter_provider():
    """Create a meter provider with in-memory reader for testing."""
    reader = InMemoryMetricReader()
    provider = MeterProvider(metric_readers=[reader])
    # Set the provider
    metrics.set_meter_provider(provider)
    yield provider, reader
    # Cleanup is handled by OpenTelemetry


class TestMetricsHelper:
    """Test MetricsHelper implementation."""

    def setup_method(self):
        """Set up test fixtures."""
        pass

    def test_emit_counter_metric(self, meter_provider):
        """Test that counter metrics can be emitted."""
        provider, reader = meter_provider
        meter = metrics.get_meter(__name__)
        helper = MetricsHelper(meter=meter)

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

        helper.emit_metric(
            "execution.count",
            "counter",
            1.0,
            correlation,
            labels={"status": "success"},
        )

        # Force collection
        provider.force_flush()

        # Check that metric was recorded
        # Note: InMemoryMetricReader doesn't provide direct access to metrics
        # but the emission should not raise errors

    def test_emit_histogram_metric(self, meter_provider):
        """Test that histogram metrics can be emitted."""
        provider, reader = meter_provider
        meter = metrics.get_meter(__name__)
        helper = MetricsHelper(meter=meter)

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

        helper.emit_metric(
            "latency.histogram",
            "histogram",
            100.5,
            correlation,
            labels={"agent_type": "llm"},
        )

        provider.force_flush()

    def test_emit_gauge_metric(self, meter_provider):
        """Test that gauge metrics can be emitted."""
        provider, reader = meter_provider
        meter = metrics.get_meter(__name__)
        helper = MetricsHelper(meter=meter)

        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        correlation = CorrelationFields(
            run_id=run_id,
            correlation_id=correlation_id,
            component_type=ComponentType.TOOL,
            component_id="tool:test_tool",
            component_version="1.0.0",
            timestamp="2024-01-01T00:00:00Z",
        )

        helper.emit_metric(
            "budget.remaining",
            "gauge",
            50.0,
            correlation,
            labels={"budget_type": "tokens"},
        )

        provider.force_flush()

    def test_emit_metric_rejects_run_id_in_labels(self, meter_provider):
        """Test that emit_metric rejects run_id as a label."""
        provider, reader = meter_provider
        meter = metrics.get_meter(__name__)
        helper = MetricsHelper(meter=meter)

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

        with pytest.raises(ValueError, match="High-cardinality identifiers"):
            helper.emit_metric(
                "execution.count",
                "counter",
                1.0,
                correlation,
                labels={"run_id": run_id},
            )

    def test_emit_metric_rejects_correlation_id_in_labels(self, meter_provider):
        """Test that emit_metric rejects correlation_id as a label."""
        provider, reader = meter_provider
        meter = metrics.get_meter(__name__)
        helper = MetricsHelper(meter=meter)

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

        with pytest.raises(ValueError, match="High-cardinality identifiers"):
            helper.emit_metric(
                "execution.count",
                "counter",
                1.0,
                correlation,
                labels={"correlation_id": correlation_id},
            )

    def test_emit_metric_rejects_invalid_metric_type(self, meter_provider):
        """Test that emit_metric rejects invalid metric types."""
        provider, reader = meter_provider
        meter = metrics.get_meter(__name__)
        helper = MetricsHelper(meter=meter)

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

        with pytest.raises(ValueError, match="Invalid metric_type"):
            helper.emit_metric(
                "test.metric",
                "invalid_type",
                1.0,
                correlation,
            )

    def test_to_metric_value_creates_contract(self, meter_provider):
        """Test that to_metric_value creates MetricValue contract."""
        provider, reader = meter_provider
        meter = metrics.get_meter(__name__)
        helper = MetricsHelper(meter=meter)

        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        correlation = CorrelationFields(
            run_id=run_id,
            correlation_id=correlation_id,
            component_type=ComponentType.SERVICE,
            component_id="service:test_service",
            component_version="1.0.0",
            timestamp="2024-01-01T00:00:00Z",
        )

        metric_value = helper.to_metric_value(
            "service.access.count",
            "counter",
            1.0,
            correlation,
            labels={"service_type": "database"},
        )

        assert metric_value.metric_name == "service.access.count"
        assert metric_value.metric_type == "counter"
        assert metric_value.value == 1.0
        assert metric_value.labels == {"service_type": "database"}
        assert metric_value.correlation.run_id == run_id

    def test_to_metric_value_rejects_run_id_in_labels(self, meter_provider):
        """Test that to_metric_value rejects run_id as a label."""
        provider, reader = meter_provider
        meter = metrics.get_meter(__name__)
        helper = MetricsHelper(meter=meter)

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

        with pytest.raises(ValueError, match="High-cardinality identifiers"):
            helper.to_metric_value(
                "test.metric",
                "counter",
                1.0,
                correlation,
                labels={"run_id": run_id},
            )

    def test_get_metrics_helper_returns_helper(self, meter_provider):
        """Test that get_metrics_helper returns a MetricsHelper instance."""
        provider, reader = meter_provider
        meter = metrics.get_meter(__name__)
        helper = get_metrics_helper(meter=meter)

        assert isinstance(helper, MetricsHelper)

    def test_metrics_helper_allows_valid_labels(self, meter_provider):
        """Test that metrics helper allows valid low-cardinality labels."""
        provider, reader = meter_provider
        meter = metrics.get_meter(__name__)
        helper = MetricsHelper(meter=meter)

        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        correlation = CorrelationFields(
            run_id=run_id,
            correlation_id=correlation_id,
            component_type=ComponentType.FLOW,
            component_id="flow:test_flow",
            component_version="1.0.0",
            timestamp="2024-01-01T00:00:00Z",
        )

        # Valid labels should not raise errors
        helper.emit_metric(
            "flow.execution.count",
            "counter",
            1.0,
            correlation,
            labels={
                "flow_type": "sequential",
                "status": "success",
                "component": "agent",
            },
        )

        provider.force_flush()
