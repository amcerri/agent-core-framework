"""Budget tracking and enforcement.

Provides budget tracking for time, calls, and cost limits.
Budget exhaustion terminates execution deterministically and
budget events are observable.
"""

import time
from datetime import datetime, timezone
from typing import Any

from agent_core.configuration.schemas import GovernanceConfig
from agent_core.contracts.errors import Error, ErrorCategory, ErrorSeverity
from agent_core.contracts.execution_context import ExecutionContext
from agent_core.contracts.observability import ComponentType, CorrelationFields
from agent_core.observability.logging import get_logger
from agent_core.utils.ids import generate_run_id


class BudgetExhaustedError(Exception):
    """Raised when budget is exhausted.

    This exception indicates that a budget limit has been exceeded
    and execution must terminate.
    """

    def __init__(
        self,
        message: str,
        budget_type: str,
        limit: float,
        consumed: float,
    ):
        """Initialize budget exhausted error.

        Args:
            message: Human-readable error message.
            budget_type: Type of budget exhausted (e.g., 'time', 'calls', 'cost').
            limit: Budget limit that was exceeded.
            consumed: Amount consumed that exceeded the limit.
        """
        super().__init__(message)
        self.budget_type = budget_type
        self.limit = limit
        self.consumed = consumed


class BudgetTracker:
    """Tracks budget consumption during execution.

    Maintains state for time, calls, and cost budgets.
    Budget tracking is deterministic and observable.
    """

    def __init__(self, context: ExecutionContext):
        """Initialize budget tracker.

        Args:
            context: Execution context containing budget limits.
        """
        self.context = context
        self.start_time = time.time()
        self.call_count = 0
        self.cost_accumulated = 0.0

        # Extract budget limits from context
        budget_config = context.budget
        self.time_limit = budget_config.get("time_limit_seconds", None)
        self.call_limit = budget_config.get("call_limit", None)
        self.cost_limit = budget_config.get("cost_limit", None)

        # Create correlation for observability
        correlation = CorrelationFields(
            run_id=context.run_id,
            correlation_id=context.correlation_id,
            component_type=ComponentType.RUNTIME,
            component_id="governance:budget",
            component_version="1.0.0",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self.logger = get_logger("agent_core.governance.budget", correlation)

        # Log budget initialization
        self.logger.debug(
            "Budget tracker initialized",
            extra={
                "time_limit": self.time_limit,
                "call_limit": self.call_limit,
                "cost_limit": self.cost_limit,
            },
        )

    def record_call(self) -> None:
        """Record a call/operation.

        Increments the call counter and checks if call limit is exceeded.
        """
        self.call_count += 1
        self.logger.debug(
            "Call recorded",
            extra={
                "call_count": self.call_count,
                "call_limit": self.call_limit,
            },
        )

    def record_cost(self, cost: float) -> None:
        """Record cost consumption.

        Args:
            cost: Cost amount to add to accumulated cost.
        """
        if cost < 0:
            raise ValueError(f"Cost cannot be negative: {cost}")

        self.cost_accumulated += cost
        self.logger.debug(
            "Cost recorded",
            extra={
                "cost": cost,
                "cost_accumulated": self.cost_accumulated,
                "cost_limit": self.cost_limit,
            },
        )

    def get_elapsed_time(self) -> float:
        """Get elapsed time since tracker initialization.

        Returns:
            Elapsed time in seconds.
        """
        return time.time() - self.start_time

    def get_call_count(self) -> int:
        """Get current call count.

        Returns:
            Number of calls recorded.
        """
        return self.call_count

    def get_cost_accumulated(self) -> float:
        """Get accumulated cost.

        Returns:
            Total cost accumulated.
        """
        return self.cost_accumulated

    def get_budget_status(self) -> dict[str, Any]:
        """Get current budget status.

        Returns:
            Dictionary with budget limits and consumption.
        """
        return {
            "time_limit": self.time_limit,
            "time_consumed": self.get_elapsed_time(),
            "call_limit": self.call_limit,
            "call_count": self.call_count,
            "cost_limit": self.cost_limit,
            "cost_accumulated": self.cost_accumulated,
        }


class BudgetEnforcer:
    """Enforces budget limits and raises errors when exhausted.

    Checks budget consumption against limits and raises BudgetExhaustedError
    when limits are exceeded. Budget enforcement is deterministic and observable.
    """

    def __init__(
        self,
        tracker: BudgetTracker,
        governance_config: GovernanceConfig | None = None,
    ):
        """Initialize budget enforcer.

        Args:
            tracker: Budget tracker instance.
            governance_config: Optional governance configuration.
        """
        self.tracker = tracker
        self.governance_config = governance_config or GovernanceConfig()

        # Create correlation for observability
        correlation = CorrelationFields(
            run_id=tracker.context.run_id,
            correlation_id=tracker.context.correlation_id,
            component_type=ComponentType.RUNTIME,
            component_id="governance:budget",
            component_version="1.0.0",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self.logger = get_logger("agent_core.governance.budget", correlation)

    def check_budget(self) -> None:
        """Check if budget limits are exceeded.

        Checks all budget types (time, calls, cost) and raises
        BudgetExhaustedError if any limit is exceeded.

        Raises:
            BudgetExhaustedError: If any budget limit is exceeded.
        """
        # Check time limit
        if self.tracker.time_limit is not None:
            elapsed = self.tracker.get_elapsed_time()
            if elapsed >= self.tracker.time_limit:
                error_message = (
                    f"Time budget exhausted: {elapsed:.2f}s >= {self.tracker.time_limit}s"
                )
                self.logger.warning(
                    "Budget exhausted: time",
                    extra={
                        "budget_type": "time",
                        "limit": self.tracker.time_limit,
                        "consumed": elapsed,
                    },
                )
                raise BudgetExhaustedError(
                    error_message,
                    budget_type="time",
                    limit=self.tracker.time_limit,
                    consumed=elapsed,
                )

        # Check call limit
        if self.tracker.call_limit is not None:
            call_count = self.tracker.get_call_count()
            if call_count >= self.tracker.call_limit:
                error_message = f"Call budget exhausted: {call_count} >= {self.tracker.call_limit}"
                self.logger.warning(
                    "Budget exhausted: calls",
                    extra={
                        "budget_type": "calls",
                        "limit": self.tracker.call_limit,
                        "consumed": call_count,
                    },
                )
                raise BudgetExhaustedError(
                    error_message,
                    budget_type="calls",
                    limit=self.tracker.call_limit,
                    consumed=call_count,
                )

        # Check cost limit
        if self.tracker.cost_limit is not None:
            cost_accumulated = self.tracker.get_cost_accumulated()
            if cost_accumulated >= self.tracker.cost_limit:
                error_message = (
                    f"Cost budget exhausted: {cost_accumulated:.4f} >= "
                    f"{self.tracker.cost_limit:.4f}"
                )
                self.logger.warning(
                    "Budget exhausted: cost",
                    extra={
                        "budget_type": "cost",
                        "limit": self.tracker.cost_limit,
                        "consumed": cost_accumulated,
                    },
                )
                raise BudgetExhaustedError(
                    error_message,
                    budget_type="cost",
                    limit=self.tracker.cost_limit,
                    consumed=cost_accumulated,
                )

        # Log budget check passed
        self.logger.debug(
            "Budget check passed",
            extra=self.tracker.get_budget_status(),
        )

    def to_error(
        self,
        budget_error: BudgetExhaustedError,
        source: str,
    ) -> Error:
        """Convert BudgetExhaustedError to structured Error.

        Args:
            budget_error: BudgetExhaustedError instance.
            source: Source component identifier.

        Returns:
            Structured Error instance.
        """
        return Error(
            error_id=generate_run_id(),  # Use run_id generator for error_id
            error_type=ErrorCategory.BUDGET_EXCEEDED,
            message=str(budget_error),
            severity=ErrorSeverity.HIGH,
            retryable=False,
            source=source,
            metadata={
                "budget_type": budget_error.budget_type,
                "limit": budget_error.limit,
                "consumed": budget_error.consumed,
            },
        )
