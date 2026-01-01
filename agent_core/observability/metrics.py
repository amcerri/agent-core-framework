"""Metrics emission with cardinality constraints.

Provides metrics emission using OpenTelemetry APIs with enforcement
of cardinality rules. High-cardinality identifiers like run_id must
not be used as metric labels.
"""

from opentelemetry import metrics
from opentelemetry.metrics import Meter

from agent_core.contracts.observability import (
    CorrelationFields,
    MetricValue,
)


class MetricsHelper:
    """Helper class for emitting metrics with cardinality constraints.

    This class provides a framework interface over OpenTelemetry metrics APIs,
    ensuring that all metrics include required correlation fields and enforce
    cardinality rules (high-cardinality identifiers must not be used as labels).

    Cardinality rules:
    - run_id must never be used as a metric label
    - correlation_id must never be used as a metric label
    - High-cardinality identifiers belong in traces or logs, not metrics
    """

    # High-cardinality fields that must not be metric labels
    FORBIDDEN_LABELS = {"run_id", "correlation_id"}

    def __init__(self, meter: Meter | None = None):
        """Initialize the metrics helper.

        Args:
            meter: OpenTelemetry meter instance. If None, uses the
                default meter from the global meter provider.
        """
        self._meter = meter or metrics.get_meter(__name__)

    def _validate_labels(self, labels: dict[str, str]) -> None:
        """Validate that labels do not include high-cardinality identifiers.

        Args:
            labels: Metric labels to validate.

        Raises:
            ValueError: If labels contain forbidden high-cardinality identifiers.
        """
        forbidden_found = self.FORBIDDEN_LABELS.intersection(labels.keys())
        if forbidden_found:
            raise ValueError(
                f"High-cardinality identifiers cannot be metric labels: {forbidden_found}. "
                "These belong in traces or logs, not metrics."
            )

    def emit_metric(
        self,
        metric_name: str,
        metric_type: str,
        value: float,
        correlation: CorrelationFields,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Emit a metric value with correlation fields.

        Args:
            metric_name: Name of the metric (e.g., 'execution.count').
            metric_type: Type of metric ('counter', 'histogram', 'gauge').
            value: Metric value.
            correlation: Required correlation fields (for reference, not as labels).
            labels: Optional metric labels (must not include high-cardinality identifiers).

        Raises:
            ValueError: If metric_type is invalid or labels contain forbidden identifiers.
        """
        # Validate labels do not include high-cardinality identifiers
        if labels is None:
            labels = {}
        self._validate_labels(labels)

        # Create metric instrument based on type
        if metric_type == "counter":
            counter = self._meter.create_counter(metric_name)
            counter.add(value, labels)
        elif metric_type == "histogram":
            histogram = self._meter.create_histogram(metric_name)
            histogram.record(value, labels)
        elif metric_type == "gauge":
            # Gauges in OpenTelemetry are typically created once and updated
            # For simplicity, we'll use an UpDownCounter as a gauge
            gauge = self._meter.create_up_down_counter(metric_name)
            gauge.add(value, labels)
        else:
            raise ValueError(
                f"Invalid metric_type: {metric_type}. "
                "Must be one of: 'counter', 'histogram', 'gauge'"
            )

    def to_metric_value(
        self,
        metric_name: str,
        metric_type: str,
        value: float,
        correlation: CorrelationFields,
        labels: dict[str, str] | None = None,
    ) -> MetricValue:
        """Convert metric parameters to MetricValue contract.

        Args:
            metric_name: Name of the metric.
            metric_type: Type of metric ('counter', 'histogram', 'gauge').
            value: Metric value.
            correlation: Required correlation fields.
            labels: Optional metric labels (validated for cardinality).

        Returns:
            MetricValue contract instance.

        Raises:
            ValueError: If labels contain forbidden identifiers.
        """
        if labels is None:
            labels = {}
        self._validate_labels(labels)

        return MetricValue(
            correlation=correlation,
            metric_name=metric_name,
            metric_type=metric_type,
            value=value,
            labels=labels,
        )


def get_metrics_helper(meter: Meter | None = None) -> MetricsHelper:
    """Get a metrics helper instance.

    Args:
        meter: Optional OpenTelemetry meter. If None, uses default meter.

    Returns:
        MetricsHelper instance.
    """
    return MetricsHelper(meter=meter)
