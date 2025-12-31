"""Base service abstraction.

Provides a base class for implementing services that conform to the Service
contract. Services provide governed access to shared resources and state.
"""

from abc import ABC, abstractmethod

from agent_core.contracts.execution_context import ExecutionContext


class BaseService(ABC):
    """Base class for service implementations.

    This class provides a foundation for implementing services that conform
    to the Service contract. Subclasses must implement the abstract methods
    to define service-specific behavior.

    Services provide governed access to shared capabilities:
    - own persistent or shared state
    - enforce access control and auditing
    - abstract vendor-specific implementations
    - provide governed access to resources

    Services:
    - are accessed by agents and tools via the runtime
    - own persistent or shared state
    - must enforce access control via check_permission
    - should abstract vendor-specific implementations

    Observability is handled by the runtime through the ExecutionContext.
    """

    @property
    @abstractmethod
    def service_id(self) -> str:
        """Unique identifier for this service.

        Returns:
            Service identifier string.
        """
        ...

    @property
    @abstractmethod
    def service_version(self) -> str:
        """Version identifier for this service.

        Returns:
            Service version string.
        """
        ...

    @property
    @abstractmethod
    def capabilities(self) -> list[str]:
        """List of capabilities this service provides.

        Returns:
            List of capability identifiers.
        """
        ...

    @abstractmethod
    def check_permission(self, action: str, context: ExecutionContext) -> bool:
        """Check if the given action is permitted for the context.

        Services must enforce access control by checking permissions
        before allowing access to shared resources or state.

        Args:
            action: The action to check (e.g., 'read', 'write').
            context: Execution context with permissions.

        Returns:
            True if the action is permitted, False otherwise.

        Notes:
            - Services should check permissions before any state access.
            - Permission checks should be deterministic and observable.
            - Failed permission checks should be logged and audited.
        """
        ...
