"""Observability contract schemas.

Defines schemas for observability signals: logs, traces, metrics, and
audit events. All signals must include required correlation fields.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ComponentType(str, Enum):
    """Component type enumeration."""

    RUNTIME = "runtime"
    AGENT = "agent"
    TOOL = "tool"
    SERVICE = "service"
    FLOW = "flow"


class LogLevel(str, Enum):
    """Log level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


class CorrelationFields(BaseModel):
    """Required correlation fields for all observability signals.

    These fields must be present in all logs, traces, metrics, and
    audit events to enable end-to-end correlation.
    """

    run_id: str = Field(
        ...,
        description="Unique identifier for a single execution lifecycle.",
    )
    correlation_id: str = Field(
        ...,
        description="Identifier used to correlate logs, traces, metrics, and audit events.",
    )
    component_type: ComponentType = Field(
        ...,
        description="Type of component emitting the signal (runtime, agent, tool, service, flow).",
    )
    component_id: str = Field(
        ...,
        description="Unique identifier of the component.",
    )
    component_version: str = Field(
        ...,
        description="Version identifier of the component.",
    )
    timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp of when the signal was emitted.",
    )


class LogEvent(BaseModel):
    """Structured log event schema.

    Logs provide human-readable diagnostic information. They must
    include correlation fields and must not include sensitive data
    by default.
    """

    correlation: CorrelationFields = Field(
        ...,
        description="Required correlation fields.",
    )
    level: LogLevel = Field(
        ...,
        description="Log level (DEBUG, INFO, WARN, ERROR).",
    )
    message: str = Field(
        ...,
        description="Concise and descriptive log message.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional log context (must not include sensitive data by default).",
    )


class SpanAttributes(BaseModel):
    """Span attributes for tracing.

    Represents attributes attached to a trace span.
    """

    component_identifiers: dict[str, str] = Field(
        default_factory=dict,
        description="Component identifiers (agent_id, tool_id, etc.).",
    )
    execution_status: str | None = Field(
        default=None,
        description="Execution status (e.g., 'success', 'error').",
    )
    duration_ms: float | None = Field(
        default=None,
        description="Duration of the operation in milliseconds.",
    )
    error_classification: dict[str, Any] | None = Field(
        default=None,
        description="Error classification if applicable.",
    )
    budget_impact: dict[str, Any] | None = Field(
        default=None,
        description="Budget impact if applicable.",
    )


class TraceSpan(BaseModel):
    """Trace span schema.

    Traces describe execution flow and causality. Spans must include
    correlation fields and attributes describing the operation.
    """

    correlation: CorrelationFields = Field(
        ...,
        description="Required correlation fields.",
    )
    span_name: str = Field(
        ...,
        description="Name of the span (e.g., 'run', 'agent.execution', 'tool.invoke').",
    )
    parent_span_id: str | None = Field(
        default=None,
        description="Identifier of the parent span, if any.",
    )
    attributes: SpanAttributes = Field(
        default_factory=SpanAttributes,
        description="Span attributes (status, duration, errors, etc.).",
    )


class MetricValue(BaseModel):
    """Metric value schema.

    Represents a single metric data point. Metrics must avoid
    high-cardinality labels (e.g., run_id must not be a label).
    """

    correlation: CorrelationFields = Field(
        ...,
        description="Required correlation fields.",
    )
    metric_name: str = Field(
        ...,
        description="Name of the metric (e.g., 'execution.count', 'latency.histogram').",
    )
    metric_type: str = Field(
        ...,
        description="Type of metric (counter, histogram, gauge).",
    )
    value: float = Field(
        ...,
        description="Metric value.",
    )
    labels: dict[str, str] = Field(
        default_factory=dict,
        description="Metric labels (must not include high-cardinality identifiers like run_id).",
    )


class AuditEvent(BaseModel):
    """Audit event schema.

    Audit events provide immutable records of security- or
    side-effect-relevant actions. They cannot be disabled in production.
    """

    correlation: CorrelationFields = Field(
        ...,
        description="Required correlation fields.",
    )
    initiator_identity: str = Field(
        ...,
        description="Identity of the initiator (from ExecutionContext).",
    )
    action: str = Field(
        ...,
        description="Action performed (e.g., 'tool.execute', 'service.read').",
    )
    target_resource: str = Field(
        ...,
        description="Target resource identifier (e.g., 'tool:my_tool', 'service:my_service').",
    )
    decision_outcome: str = Field(
        ...,
        description="Decision outcome (e.g., 'allowed', 'denied', 'approved').",
    )
    policy_or_permission: str | None = Field(
        default=None,
        description="Associated policy or permission identifier, if applicable.",
    )
