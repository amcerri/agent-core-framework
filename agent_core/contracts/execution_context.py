"""Execution Context contract.

Defines the schema for ExecutionContext, which carries all cross-cutting
concerns required to execute agents, tools, and flows in a controlled
and observable manner.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class ExecutionContext(BaseModel):
    """Execution context schema.

    Carries all cross-cutting concerns required to execute agents, tools,
    and flows in a controlled and observable manner. Created by the runtime
    and propagated immutably.

    All fields are mandatory at runtime.
    """

    model_config = {"frozen": True, "extra": "forbid"}

    run_id: str = Field(
        ...,
        description="Unique identifier for a single execution lifecycle.",
    )
    correlation_id: str = Field(
        ...,
        description=("Identifier used to correlate logs, traces, metrics, and audit events."),
    )
    initiator: str = Field(
        ...,
        description="Identity of the caller (user, system, or service).",
    )
    permissions: dict[str, Any] = Field(
        ...,
        description="Effective permission set resolved by governance.",
    )
    budget: dict[str, Any] = Field(
        ...,
        description="Time, call, and cost limits for the execution.",
    )
    locale: str = Field(
        ...,
        description="Language and regional preferences for outputs.",
    )
    observability: dict[str, Any] = Field(
        ...,
        description="Trace and logging propagation metadata.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Free-form, non-authoritative contextual data.",
    )

    @field_validator("run_id", "correlation_id")
    @classmethod
    def validate_uuid_format(cls, v: str) -> str:
        """Validate that run_id and correlation_id are valid UUIDs."""
        import uuid

        try:
            uuid.UUID(v)
        except ValueError as e:
            raise ValueError(f"Invalid UUID format: {v}. Must be a valid UUID v4.") from e
        return v
