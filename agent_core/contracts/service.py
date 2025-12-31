"""Service contract.

Defines the interface for services, which provide governed access to
shared capabilities including state and memory.
"""

from typing import Protocol

from agent_core.contracts.execution_context import ExecutionContext


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
