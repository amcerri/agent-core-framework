"""Flow contract.

Defines the interface and schemas for flows, which define explicit
orchestration logic.
"""

from typing import Any, Protocol

from pydantic import BaseModel, Field


class FlowState(BaseModel):
    """Flow state schema.

    Represents the current state of a flow execution.
    """

    current_node: str = Field(
        ...,
        description="Identifier of the current node in the flow.",
    )
    state_data: dict[str, Any] = Field(
        default_factory=dict,
        description="State data accumulated during flow execution.",
    )
    history: list[dict[str, Any]] = Field(
        default_factory=list,
        description="History of nodes executed in the flow.",
    )


class Flow(Protocol):
    """Flow interface protocol.

    Flows define explicit orchestration logic. They are declarative,
    separate from agent logic, and must be inspectable and replayable.

    Flows must:
    - be declarative
    - not contain business logic
    - be inspectable and replayable
    """

    @property
    def flow_id(self) -> str:
        """Unique identifier for this flow."""
        ...

    @property
    def flow_version(self) -> str:
        """Version identifier for this flow."""
        ...

    @property
    def entrypoint(self) -> str:
        """Identifier of the entry point node."""
        ...

    @property
    def nodes(self) -> dict[str, dict[str, Any]]:
        """Dictionary of node definitions keyed by node identifier."""
        ...

    @property
    def transitions(self) -> list[dict[str, Any]]:
        """List of transition definitions between nodes."""
        ...
