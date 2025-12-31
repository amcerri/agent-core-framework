"""Base agent abstraction.

Provides a base class for implementing agents that conform to the Agent
contract. Agents are decision-making units and must not perform I/O or
orchestration directly.
"""

from abc import ABC, abstractmethod

from agent_core.contracts.agent import AgentInput, AgentResult
from agent_core.contracts.execution_context import ExecutionContext


class BaseAgent(ABC):
    """Base class for agent implementations.

    This class provides a foundation for implementing agents that conform
    to the Agent contract. Subclasses must implement the abstract methods
    to define agent-specific behavior.

    Agents are decision-making units that:
    - interpret inputs within a given context
    - decide which actions to take
    - return structured outputs with requested actions

    Agents must not:
    - access external systems directly (use tools via runtime)
    - orchestrate other agents directly
    - manage retries, policies, or logging (handled by runtime)
    - mutate shared state directly (use services via runtime)

    Observability is handled by the runtime through the ExecutionContext.
    """

    @property
    @abstractmethod
    def agent_id(self) -> str:
        """Unique identifier for this agent.

        Returns:
            Agent identifier string.
        """
        ...

    @property
    @abstractmethod
    def agent_version(self) -> str:
        """Version identifier for this agent.

        Returns:
            Agent version string.
        """
        ...

    @property
    @abstractmethod
    def capabilities(self) -> list[str]:
        """List of capabilities this agent provides.

        Returns:
            List of capability identifiers.
        """
        ...

    @abstractmethod
    def run(self, input_data: AgentInput, context: ExecutionContext) -> AgentResult:
        """Execute the agent with the given input and context.

        This is the main entry point for agent execution. The runtime
        invokes this method with validated input and execution context.

        Args:
            input_data: Structured input data for the agent.
            context: Execution context with permissions, budget, etc.

        Returns:
            AgentResult containing status, output, actions, errors, and metrics.

        Notes:
            - Agents should not perform I/O directly in this method.
            - Tool invocations should be requested via the actions field.
            - The runtime will execute requested actions and provide results
              in subsequent invocations if needed.
        """
        ...
