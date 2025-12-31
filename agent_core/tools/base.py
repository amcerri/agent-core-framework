"""Base tool abstraction.

Provides a base class for implementing tools that conform to the Tool
contract. Tools encapsulate side effects and external interactions.
"""

from abc import ABC, abstractmethod

from agent_core.contracts.execution_context import ExecutionContext
from agent_core.contracts.tool import ToolInput, ToolResult


class BaseTool(ABC):
    """Base class for tool implementations.

    This class provides a foundation for implementing tools that conform
    to the Tool contract. Subclasses must implement the abstract methods
    to define tool-specific behavior.

    Tools are execution units that:
    - perform a single, well-defined capability
    - encapsulate side effects or external interactions
    - validate inputs and outputs
    - respect timeouts and budgets
    - surface structured errors

    Tools:
    - are invoked by agents via the runtime
    - are stateless by default
    - must declare all required permissions
    - should be deterministic for the same input where possible

    Observability is handled by the runtime through the ExecutionContext.
    """

    @property
    @abstractmethod
    def tool_id(self) -> str:
        """Unique identifier for this tool.

        Returns:
            Tool identifier string.
        """
        ...

    @property
    @abstractmethod
    def tool_version(self) -> str:
        """Version identifier for this tool.

        Returns:
            Tool version string.
        """
        ...

    @property
    @abstractmethod
    def permissions_required(self) -> list[str]:
        """List of permissions required to execute this tool.

        Returns:
            List of permission identifiers required for execution.
        """
        ...

    @abstractmethod
    def execute(self, input_data: ToolInput, context: ExecutionContext) -> ToolResult:
        """Execute the tool with the given input and context.

        This is the main entry point for tool execution. The runtime
        invokes this method after validating permissions and budgets.

        Args:
            input_data: Structured input data for the tool.
            context: Execution context with permissions, budget, etc.

        Returns:
            ToolResult containing status, output, errors, and metrics.

        Notes:
            - Tools should validate inputs before execution.
            - Tools should respect timeout constraints from input_data.
            - Tools should surface errors in the errors field of ToolResult.
            - Tools should record execution metrics in the metrics field.
        """
        ...
