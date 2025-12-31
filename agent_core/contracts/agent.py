"""Agent contract.

Defines the interface and schemas for agents, which are decision-making
units operating purely within the Execution Context.
"""

from typing import Any, Protocol

from pydantic import BaseModel, Field

from agent_core.contracts.execution_context import ExecutionContext


class AgentInput(BaseModel):
    """Agent input schema.

    Structured input data for agent execution.
    """

    payload: dict[str, Any] = Field(
        ...,
        description="Structured input data.",
    )
    history: list[dict[str, Any]] | None = Field(
        default=None,
        description="Optional prior interaction context.",
    )


class AgentResult(BaseModel):
    """Agent result schema.

    Structured output from agent execution.
    """

    status: str = Field(
        ...,
        description="Execution status (e.g., 'success', 'error', 'pending').",
    )
    output: dict[str, Any] = Field(
        ...,
        description="Structured output data.",
    )
    actions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Actions requested by the agent (e.g., tool invocations).",
    )
    errors: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Errors encountered during execution.",
    )
    metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="Execution metrics (latency, token usage, etc.).",
    )


class Agent(Protocol):
    """Agent interface protocol.

    Agents are decision-making units operating purely within the
    Execution Context. They interpret inputs, decide which actions
    to take, and produce structured outputs.

    Agents must not:
    - access external systems directly
    - manage retries or persistence
    - mutate shared state directly
    """

    @property
    def agent_id(self) -> str:
        """Unique identifier for this agent."""
        ...

    @property
    def agent_version(self) -> str:
        """Version identifier for this agent."""
        ...

    @property
    def capabilities(self) -> list[str]:
        """List of capabilities this agent provides."""
        ...

    def run(self, input_data: AgentInput, context: ExecutionContext) -> AgentResult:
        """Execute the agent with the given input and context.

        Args:
            input_data: Structured input data for the agent.
            context: Execution context with permissions, budget, etc.

        Returns:
            AgentResult containing status, output, actions, errors, and metrics.
        """
        ...
