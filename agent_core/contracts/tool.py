"""Tool contract.

Defines the interface and schemas for tools, which encapsulate side effects
or external interactions.
"""

from typing import Any, Protocol

from pydantic import BaseModel, Field

from agent_core.contracts.execution_context import ExecutionContext


class ToolInput(BaseModel):
    """Tool input schema.

    Structured input data for tool execution.
    """

    payload: dict[str, Any] = Field(
        ...,
        description="Structured input data for the tool.",
    )
    timeout: float | None = Field(
        default=None,
        description="Timeout in seconds for tool execution.",
    )
    retry_policy: dict[str, Any] | None = Field(
        default=None,
        description="Retry policy configuration.",
    )


class ToolResult(BaseModel):
    """Tool result schema.

    Structured output from tool execution.
    """

    status: str = Field(
        ...,
        description="Execution status (e.g., 'success', 'error', 'timeout').",
    )
    output: dict[str, Any] = Field(
        ...,
        description="Structured output data from the tool.",
    )
    errors: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Errors encountered during execution.",
    )
    metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="Execution metrics (latency, resource usage, etc.).",
    )


class Tool(Protocol):
    """Tool interface protocol.

    Tools encapsulate side effects or external interactions. They are
    invoked by agents via the runtime and must declare required permissions.

    Tools must:
    - be deterministic for the same input where possible
    - declare all required permissions
    - emit structured observability signals
    """

    @property
    def tool_id(self) -> str:
        """Unique identifier for this tool."""
        ...

    @property
    def tool_version(self) -> str:
        """Version identifier for this tool."""
        ...

    @property
    def permissions_required(self) -> list[str]:
        """List of permissions required to execute this tool."""
        ...

    def execute(self, input_data: ToolInput, context: ExecutionContext) -> ToolResult:
        """Execute the tool with the given input and context.

        Args:
            input_data: Structured input data for the tool.
            context: Execution context with permissions, budget, etc.

        Returns:
            ToolResult containing status, output, errors, and metrics.
        """
        ...
