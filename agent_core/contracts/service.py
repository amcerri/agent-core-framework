"""Service contract.

Defines the interface for services, which provide governed access to
shared capabilities including state and memory.
"""

from typing import Any, Protocol

from pydantic import BaseModel, Field

from agent_core.contracts.execution_context import ExecutionContext


class ServiceInput(BaseModel):
    """Service input schema.

    Structured input data for service execution.
    """

    action: str = Field(
        ...,
        description="Action to execute (e.g., 'read', 'write', 'get', 'set').",
    )
    payload: dict[str, Any] = Field(
        ...,
        description="Structured input data for the service action.",
    )


class ServiceResult(BaseModel):
    """Service result schema.

    Structured output from service execution.
    """

    status: str = Field(
        ...,
        description="Execution status (e.g., 'success', 'error').",
    )
    output: dict[str, Any] = Field(
        ...,
        description="Structured output data from the service.",
    )
    errors: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Errors encountered during execution.",
    )
    metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="Execution metrics (latency, resource usage, etc.).",
    )


class Service(Protocol):
    """Service interface protocol.

    Services provide governed access to shared capabilities, including
    state and memory. They enforce access control and auditing, and
    abstract vendor-specific implementations.

    Services must:
    - own persistent or shared state
    - enforce access control and auditing
    - abstract vendor-specific implementations
    """

    @property
    def service_id(self) -> str:
        """Unique identifier for this service."""
        ...

    @property
    def service_version(self) -> str:
        """Version identifier for this service."""
        ...

    @property
    def capabilities(self) -> list[str]:
        """List of capabilities this service provides."""
        ...

    def check_permission(self, action: str, context: ExecutionContext) -> bool:
        """Check if the given action is permitted for the context.

        Args:
            action: The action to check (e.g., 'read', 'write').
            context: Execution context with permissions.

        Returns:
            True if the action is permitted, False otherwise.
        """
        ...

    def execute(self, input_data: ServiceInput, context: ExecutionContext) -> ServiceResult:
        """Execute a service action with the given input and context.

        Args:
            input_data: Structured input data containing action and payload.
            context: Execution context with permissions, budget, etc.

        Returns:
            ServiceResult containing status, output, errors, and metrics.
        """
        ...
