"""Error model contract.

Defines structured error schemas and error categories. Errors are
first-class structured objects, not exceptions.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ErrorCategory(str, Enum):
    """Error category enumeration.

    Defines the standard error categories used throughout the framework.
    """

    VALIDATION_ERROR = "validation_error"
    PERMISSION_ERROR = "permission_error"
    BUDGET_EXCEEDED = "budget_exceeded"
    TIMEOUT = "timeout"
    EXECUTION_FAILURE = "execution_failure"
    DEPENDENCY_FAILURE = "dependency_failure"


class ErrorSeverity(str, Enum):
    """Error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Error(BaseModel):
    """Error schema.

    Errors are first-class structured objects that propagate with
    full context. Retryable errors may be retried by the runtime;
    non-retryable errors terminate execution.
    """

    error_id: str = Field(
        ...,
        description="Unique identifier for this error instance.",
    )
    error_type: ErrorCategory = Field(
        ...,
        description="Category of the error.",
    )
    message: str = Field(
        ...,
        description="Human-readable error message.",
    )
    severity: ErrorSeverity = Field(
        ...,
        description="Severity level of the error.",
    )
    retryable: bool = Field(
        ...,
        description="Whether this error is retryable.",
    )
    source: str = Field(
        ...,
        description=(
            "Source component that generated the error (e.g., 'agent:my_agent', 'tool:my_tool')."
        ),
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional error context and metadata.",
    )
