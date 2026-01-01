"""Tracing primitives using OpenTelemetry APIs.

Provides span creation and management helpers that use OpenTelemetry APIs
behind framework interfaces. Exporter configuration is optional, allowing
the framework to run without external backends.
"""

from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, Tracer

from agent_core.contracts.observability import (
    CorrelationFields,
    SpanAttributes,
    TraceSpan,
)


class TracingHelper:
    """Helper class for creating and managing trace spans.

    This class provides a framework interface over OpenTelemetry APIs,
    ensuring that all spans include required correlation fields and attributes.
    """

    def __init__(self, tracer: Tracer | None = None):
        """Initialize the tracing helper.

        Args:
            tracer: OpenTelemetry tracer instance. If None, uses the
                default tracer from the global tracer provider.
        """
        self._tracer = tracer or trace.get_tracer(__name__)

    def create_span(
        self,
        span_name: str,
        correlation: CorrelationFields,
        parent_span_id: str | None = None,
        attributes: SpanAttributes | None = None,
    ) -> trace.Span:
        """Create a trace span with correlation fields.

        Args:
            span_name: Name of the span (e.g., 'run', 'agent.execution').
            correlation: Required correlation fields.
            parent_span_id: Optional parent span identifier (for reference).
            attributes: Optional span attributes.

        Returns:
            OpenTelemetry span instance with correlation fields set as attributes.
        """
        # Build span attributes from correlation fields and span attributes
        span_attrs: dict[str, Any] = {
            "run_id": correlation.run_id,
            "correlation_id": correlation.correlation_id,
            "component_type": correlation.component_type.value,
            "component_id": correlation.component_id,
            "component_version": correlation.component_version,
        }

        # Add span attributes if provided
        if attributes:
            if attributes.component_identifiers:
                span_attrs.update(attributes.component_identifiers)
            if attributes.execution_status:
                span_attrs["execution_status"] = attributes.execution_status
            if attributes.duration_ms is not None:
                span_attrs["duration_ms"] = attributes.duration_ms
            if attributes.error_classification:
                span_attrs["error_classification"] = attributes.error_classification
            if attributes.budget_impact:
                span_attrs["budget_impact"] = attributes.budget_impact

        # Create span (OpenTelemetry handles parent context automatically)
        span = self._tracer.start_span(span_name, attributes=span_attrs)

        return span

    @contextmanager
    def span(
        self,
        span_name: str,
        correlation: CorrelationFields,
        parent_span_id: str | None = None,
        attributes: SpanAttributes | None = None,
    ):
        """Context manager for creating and managing a span.

        Args:
            span_name: Name of the span.
            correlation: Required correlation fields.
            parent_span_id: Optional parent span identifier (for reference).
            attributes: Optional span attributes.

        Yields:
            OpenTelemetry span instance.
        """
        span = self.create_span(span_name, correlation, parent_span_id, attributes)
        try:
            yield span
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise
        finally:
            span.end()

    def to_trace_span(
        self,
        span: trace.Span,
        correlation: CorrelationFields,
        span_name: str,
        parent_span_id: str | None = None,
    ) -> TraceSpan:
        """Convert an OpenTelemetry span to a TraceSpan contract.

        Args:
            span: OpenTelemetry span instance.
            correlation: Correlation fields.
            span_name: Name of the span.
            parent_span_id: Optional parent span identifier.

        Returns:
            TraceSpan contract instance.
        """
        # Extract attributes from span context
        span_context = span.get_span_context()
        parent_id = None
        if parent_span_id:
            parent_id = parent_span_id
        elif span_context and span_context.trace_flags:
            # Use span context trace ID as parent reference if available
            parent_id = format(span_context.trace_id, "032x")

        # Build span attributes from span's attributes
        span_attrs = SpanAttributes()

        # Note: OpenTelemetry spans store attributes internally
        # In a real implementation, we would extract them here
        # For now, we return the contract with empty attributes
        # as the span itself contains the correlation fields

        return TraceSpan(
            correlation=correlation,
            span_name=span_name,
            parent_span_id=parent_id,
            attributes=span_attrs,
        )


def get_tracing_helper(tracer: Tracer | None = None) -> TracingHelper:
    """Get a tracing helper instance.

    Args:
        tracer: Optional OpenTelemetry tracer. If None, uses default tracer.

    Returns:
        TracingHelper instance.
    """
    return TracingHelper(tracer=tracer)
