"""Unit tests for tracing primitives."""

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from agent_core.contracts.observability import (
    ComponentType,
    CorrelationFields,
    SpanAttributes,
)
from agent_core.observability.tracing import TracingHelper, get_tracing_helper
from agent_core.utils.ids import generate_correlation_id, generate_run_id


@pytest.fixture
def tracer_provider():
    """Create a tracer provider with in-memory exporter for testing."""
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    # Temporarily set the provider
    original_provider = trace._TRACER_PROVIDER
    trace._TRACER_PROVIDER = provider
    yield provider, exporter
    # Restore original provider
    trace._TRACER_PROVIDER = original_provider


class TestTracingHelper:
    """Test TracingHelper implementation."""

    def setup_method(self):
        """Set up test fixtures."""
        pass

    def test_create_span_includes_correlation_fields(self, tracer_provider):
        """Test that created spans include correlation fields."""
        provider, exporter = tracer_provider
        tracer = trace.get_tracer(__name__)
        helper = TracingHelper(tracer=tracer)

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

        span = helper.create_span("agent.execution", correlation)
        span.end()

        # Check exported spans
        spans = exporter.get_finished_spans()
        assert len(spans) == 1

        span_data = spans[0]
        assert span_data.name == "agent.execution"
        assert span_data.attributes["run_id"] == run_id
        assert span_data.attributes["correlation_id"] == correlation_id
        assert span_data.attributes["component_type"] == "agent"
        assert span_data.attributes["component_id"] == "agent:test_agent"
        assert span_data.attributes["component_version"] == "1.0.0"

    def test_create_span_includes_attributes(self, tracer_provider):
        """Test that created spans include span attributes."""
        provider, exporter = tracer_provider
        tracer = trace.get_tracer(__name__)
        helper = TracingHelper(tracer=tracer)

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

        attributes = SpanAttributes(
            component_identifiers={"tool_id": "test_tool"},
            execution_status="success",
            duration_ms=100.5,
        )

        span = helper.create_span("tool.invoke", correlation, attributes=attributes)
        span.end()

        spans = exporter.get_finished_spans()
        assert len(spans) == 1

        span_data = spans[0]
        assert span_data.attributes["tool_id"] == "test_tool"
        assert span_data.attributes["execution_status"] == "success"
        assert span_data.attributes["duration_ms"] == 100.5

    def test_span_context_manager(self, tracer_provider):
        """Test that span context manager works correctly."""
        provider, exporter = tracer_provider
        tracer = trace.get_tracer(__name__)
        helper = TracingHelper(tracer=tracer)

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

        with helper.span("run", correlation) as span:
            assert span is not None
            assert span.is_recording()

        spans = exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].name == "run"

    def test_span_context_manager_handles_exceptions(self, tracer_provider):
        """Test that span context manager handles exceptions correctly."""
        provider, exporter = tracer_provider
        tracer = trace.get_tracer(__name__)
        helper = TracingHelper(tracer=tracer)

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

        with pytest.raises(ValueError):
            with helper.span("run", correlation):
                raise ValueError("Test error")

        spans = exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].status.status_code.name == "ERROR"

    def test_to_trace_span_converts_correctly(self, tracer_provider):
        """Test that to_trace_span converts OpenTelemetry span to contract."""
        provider, exporter = tracer_provider
        tracer = trace.get_tracer(__name__)
        helper = TracingHelper(tracer=tracer)

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

        opentelemetry_span = helper.create_span("flow.execution", correlation)
        trace_span = helper.to_trace_span(opentelemetry_span, correlation, "flow.execution")
        opentelemetry_span.end()

        assert trace_span.correlation.run_id == run_id
        assert trace_span.correlation.correlation_id == correlation_id
        assert trace_span.span_name == "flow.execution"
        assert isinstance(trace_span.attributes, SpanAttributes)

    def test_get_tracing_helper_returns_helper(self, tracer_provider):
        """Test that get_tracing_helper returns a TracingHelper instance."""
        provider, exporter = tracer_provider
        tracer = trace.get_tracer(__name__)
        helper = get_tracing_helper(tracer=tracer)

        assert isinstance(helper, TracingHelper)

    def test_spans_for_different_component_types(self, tracer_provider):
        """Test that spans can be created for different component types."""
        provider, exporter = tracer_provider
        tracer = trace.get_tracer(__name__)
        helper = TracingHelper(tracer=tracer)

        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        component_types = [
            (ComponentType.RUNTIME, "run"),
            (ComponentType.FLOW, "flow.execution"),
            (ComponentType.AGENT, "agent.execution"),
            (ComponentType.TOOL, "tool.invoke"),
            (ComponentType.SERVICE, "service.access"),
        ]

        for component_type, span_name in component_types:
            correlation = CorrelationFields(
                run_id=run_id,
                correlation_id=correlation_id,
                component_type=component_type,
                component_id=f"{component_type.value}:test",
                component_version="1.0.0",
                timestamp="2024-01-01T00:00:00Z",
            )

            span = helper.create_span(span_name, correlation)
            span.end()

        spans = exporter.get_finished_spans()
        assert len(spans) == len(component_types)

        for i, (component_type, span_name) in enumerate(component_types):
            assert spans[i].name == span_name
            assert spans[i].attributes["component_type"] == component_type.value
